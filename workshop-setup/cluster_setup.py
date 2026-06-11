"""Create the workshop's classic compute cluster with the Databricks SDK.

Backs the optional automation cell in workshop_setup.ipynb: creates (or finds)
the cluster, starts it, and installs the Neo4j Spark Connector plus the Python
libraries the labs need.
"""

import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import (
    AwsAttributes,
    AwsAvailability,
    DataSecurityMode,
    EbsVolumeType,
    Library,
    MavenLibrary,
    PythonPyPiLibrary,
    State,
)

try:
    from databricks.sdk.service.compute import LibraryInstallStatus
except ImportError:
    # databricks-sdk < 0.21.0 uses the old enum name
    from databricks.sdk.service.compute import (
        LibraryFullStatusStatus as LibraryInstallStatus,
    )

CLUSTER_NAME = "Small Spark 4.0"
SPARK_VERSION = "17.3.x-cpu-ml-scala2.13"  # 17.3 LTS ML (Spark 4.0)
NODE_TYPE = "m5.large"  # AWS default; use the 2-core, 8 GB equivalent on Azure or GCP
AUTOTERMINATION_MINUTES = 30
# Connector 5.4.3 is the latest for_spark_3 build; extensively tested to work
# with Spark 4.0 on Databricks Runtime 17.3 LTS ML.
MAVEN_COORDINATES = "org.neo4j:neo4j-connector-apache-spark_2.13:5.4.3_for_spark_3"
PYPI_PACKAGES = [
    "neo4j==6.2.0",
    "databricks-agents>=1.11.0",
    "langgraph==1.2.4",
    "langchain-openai==1.3.0",
    "pydantic==2.13.4",
    "langchain-core>=1.4.6",
    "databricks-langchain>=0.20.0",
    "dspy>=3.2.1",
    "neo4j-graphrag>=1.17.0",
    "beautifulsoup4>=4.15.0",
    "sentence_transformers",
]

# m5 instances have no local disk, so the Clusters API requires an explicit EBS
# volume (the UI adds one automatically). On-demand availability keeps the
# single node (which hosts the driver) from being reclaimed as a spot instance
# mid-lab. Set to None on Azure or GCP.
AWS_ATTRIBUTES = AwsAttributes(
    availability=AwsAvailability.ON_DEMAND,
    ebs_volume_type=EbsVolumeType.GENERAL_PURPOSE_SSD,
    ebs_volume_count=1,
    ebs_volume_size=100,  # GB; the API minimum for general purpose SSD
)


def get_or_create_cluster(client: WorkspaceClient, user_email: str) -> str:
    """Find the workshop cluster by name, starting or creating it as needed."""
    for cluster in client.clusters.list():
        if cluster.cluster_name == CLUSTER_NAME and cluster.cluster_id:
            print(f"Found existing cluster {cluster.cluster_id} (state: {cluster.state})")
            if cluster.state == State.TERMINATED:
                client.clusters.start(cluster.cluster_id)
            return cluster.cluster_id

    print(f"Creating cluster '{CLUSTER_NAME}'...")
    response = client.clusters.create(
        cluster_name=CLUSTER_NAME,
        spark_version=SPARK_VERSION,
        node_type_id=NODE_TYPE,
        driver_node_type_id=NODE_TYPE,
        num_workers=0,
        data_security_mode=DataSecurityMode.SINGLE_USER,
        single_user_name=user_email,
        autotermination_minutes=AUTOTERMINATION_MINUTES,
        aws_attributes=AWS_ATTRIBUTES,
        spark_conf={
            "spark.databricks.cluster.profile": "singleNode",
            "spark.master": "local[*]",
        },
        custom_tags={"ResourceClass": "SingleNode"},
    )
    if not response.cluster_id:
        raise RuntimeError("Cluster creation returned no cluster ID")
    return response.cluster_id


def wait_for_cluster_running(
    client: WorkspaceClient, cluster_id: str, timeout_seconds: int = 900
) -> None:
    """Poll until the cluster reaches RUNNING."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        cluster = client.clusters.get(cluster_id)
        print(f"  Cluster state: {cluster.state}")
        if cluster.state == State.RUNNING:
            return
        if cluster.state in (State.TERMINATED, State.ERROR, State.UNKNOWN):
            raise RuntimeError(f"Cluster entered {cluster.state}: {cluster.state_message}")
        time.sleep(20)
    raise TimeoutError(f"Cluster did not start within {timeout_seconds} seconds")


def install_and_wait_for_libraries(
    client: WorkspaceClient, cluster_id: str, timeout_seconds: int = 900
) -> None:
    """Install the Maven and PyPI libraries, then poll until none are pending."""
    PENDING_STATES = (
        LibraryInstallStatus.PENDING,
        LibraryInstallStatus.RESOLVING,
        LibraryInstallStatus.INSTALLING,
    )

    statuses = list(client.libraries.cluster_status(cluster_id))
    if statuses and not any(
        s.status in PENDING_STATES or s.status == LibraryInstallStatus.FAILED
        for s in statuses
    ):
        print(f"{len(statuses)} libraries already installed, skipping installation")
        return

    libraries = [Library(maven=MavenLibrary(coordinates=MAVEN_COORDINATES))]
    libraries += [Library(pypi=PythonPyPiLibrary(package=p)) for p in PYPI_PACKAGES]
    client.libraries.install(cluster_id=cluster_id, libraries=libraries)
    print(f"Requested installation of {len(libraries)} libraries")

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        statuses = list(client.libraries.cluster_status(cluster_id))
        pending = [s for s in statuses if s.status in PENDING_STATES]
        failed = [s for s in statuses if s.status == LibraryInstallStatus.FAILED]
        installed = len(statuses) - len(pending) - len(failed)
        print(
            f"  {installed}/{len(statuses)} installed, "
            f"{len(pending)} pending, {len(failed)} failed"
        )
        if not pending:
            if failed:
                details = "; ".join(f"{s.library} ({s.messages})" for s in failed)
                raise RuntimeError(f"{len(failed)} libraries failed to install: {details}")
            return
        time.sleep(20)
    raise TimeoutError(f"Libraries did not finish installing within {timeout_seconds} seconds")


def create_workshop_cluster() -> str:
    """Create (or find) the workshop cluster, start it, and install all libraries."""
    client = WorkspaceClient()
    user_email = client.current_user.me().user_name
    cluster_id = get_or_create_cluster(client, user_email)
    wait_for_cluster_running(client, cluster_id)
    install_and_wait_for_libraries(client, cluster_id)
    return cluster_id
