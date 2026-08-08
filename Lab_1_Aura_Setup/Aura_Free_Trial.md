# Neo4j AuraDB Free Signup

Follow these steps to create a free Neo4j Aura account and an AuraDB Free database instance:

1. Navigate to [https://console-preview.neo4j.io/](https://console-preview.neo4j.io/)

2. Click on **"Don't have an account? Sign up"** below the login form.

3. Follow the sign-up process to create your Neo4j Aura account. You will need to provide your email address, create a password, and agree to the terms of service.

4. When prompted "Where do you want your instance deployed?", configure the following:
   - **Cloud provider:** AWS
   - **Region:** Europe, Paris (eu-west-3)

   Do **not** click **Start 14-day free trial**. That button provisions an AuraDB Professional trial instance, which expires after 14 days. This workshop uses AuraDB Free. Below the button, under "Not looking to start a free trial?", click **Select another instance type**.

   ![Instance deployment configuration showing AWS cloud provider and Europe Paris region](images/FREE_01_WHERE.png)

5. Choose the **AuraDB Free** tier, then confirm to create the instance. The confirm button is labelled **Next** or **Create instance**, depending on which version of the console you land on.

6. Your AuraDB Free instance will be created automatically. **Save your credentials immediately** - click **Download to continue** to save the credentials file. The password is only shown once.

   ![Creating your instance screen showing credentials with download option](images/FREE_02_Create_Instances.png)

7. Once your instance is running, you will see it in the Instances list with a "RUNNING" status and a type of **AuraDB Free**. Copy the connection string, which looks like `neo4j+s://xxxxxxxx.databases.neo4j.io`. You will need it, your username `neo4j`, and the downloaded password in every later lab.

## What AuraDB Free Gives You

AuraDB Free holds up to **200,000 nodes** and **400,000 relationships**. It stays free, needs no credit card, and does not expire.

The workshop fits comfortably inside that. After finishing Labs 1 through 3 your graph holds about 21,613 nodes, which is 10.8 percent of the node cap.

Two limits worth knowing. You can create only one Free instance per account. A Free instance with no activity for 30 days is deleted, so keep using it while the workshop runs.

## What AuraDB Free Does Not Include

Graph Data Science is not available on AuraDB Free. `Lab_2_Databricks_ETL_Neo4j/02_gds_knn_aircraft.ipynb` is therefore optional and skippable: skip it unless you have your own AuraDB Professional instance. Every other notebook in the workshop runs on AuraDB Free.

---

**Next:** Return to the [Lab 1 README](README.md) to practice Cypher basics.
