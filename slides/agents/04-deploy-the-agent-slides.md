---
marp: true
theme: default
paginate: true
---

<style>
section {
  --marp-auto-scaling-code: false;
}

li {
  opacity: 1 !important;
  animation: none !important;
  visibility: visible !important;
}

/* Disable all fragment animations */
.marp-fragment {
  opacity: 1 !important;
  visibility: visible !important;
}

ul > li,
ol > li {
  opacity: 1 !important;
}
</style>

# Deploying the Agent

From a notebook that works to a product that works for someone else

<!--
The supervisor graph already works. This deck is not about the
graph, the three tools, or the routing prompt. It starts where
notebook 01 of Lab 5 ends.

The audience for this deck is different from the audience for the
supervisor deck. That one is for whoever writes the graph. This
one is for whoever has to sit across from a security reviewer and
explain what the endpoint is allowed to touch and why.
-->

---

## What Actually Changes

- **A notebook demo runs with your permissions.** It works because you happen to have them
- **An endpoint runs as its own identity**, a service principal that Model Serving creates
- **That principal starts with access to nothing.** Every resource it touches has to be granted to that identity explicitly
- **That is the whole line** between a notebook that works and a product that works for someone else

<!--
This is the thesis, and if the day runs short and only one slide
survives, it is this one.

Nothing about the agent's logic changes when it is deployed. What
changes is who is asking. In the notebook, every Databricks call
runs as the participant. On the endpoint, every call runs as a
principal that was created for the endpoint and that has been
granted nothing by default.

Everything else in this deck is the mechanics of turning that
sentence into a list of grants a reviewer can read.
-->

---

## Who the Endpoint Is

The questions a security reviewer asks, and where each answer lives.

| Question | Answer |
|---|---|
| Who is the caller? | A service principal Model Serving creates for the endpoint |
| What can it reach? | Only the resources declared at log time |
| Where is that declared? | `build_resources` in `agent.py`, logged with the model |
| How is it granted? | MLflow grants the principal that list at deploy time |
| Where do secrets live? | A Databricks secret scope, referenced, never copied |
| What is auditable? | A Unity Catalog model version and an MLflow trace per request |

<!--
Put this slide early on purpose. It is the slide a reviewer would
ask you to build, so build it once and keep it.

Note the shape of the answer: the permission surface is a list in
a file, checked into the repository, logged next to the model
version. It is not workspace state somebody clicked. That is what
makes it reviewable.

The next slides are just this table expanded.
-->

---

## The Wrapper: MLflow `ResponsesAgent`

The graph is not served directly. It is wrapped.

```python
class FleetOpsAgent(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse: ...
    def predict_stream(self, request: ResponsesAgentRequest) -> Iterator[...]: ...

AGENT = FleetOpsAgent()
set_model(AGENT)
```

- **A compiled graph is an object in memory**, holding an open driver and a live session
- **`ResponsesAgent` is the interface Model Serving speaks**: one request in, output items out
- **`set_model(AGENT)`** is the line that makes the file the model rather than a library beside it

<!--
A LangGraph object cannot be handed to Model Serving. It has to be
rebuilt from nothing on a machine nobody has logged into. The
wrapper is what makes that possible: it is a class with a known
interface that can construct itself at startup.

ResponsesAgent gives two methods. predict answers one question.
predict_stream exists so a Responses API client that only speaks
streaming still works, even though this graph has no token stream
to forward: every node returns a whole finding and the answer is
written in one call at the end.

Worth noting from agent.py: the connections are opened on the
first request rather than at load time. A container that fails
while loading restarts, fails again, and leaves an endpoint that
never reaches READY with the reason buried in build logs. A
container that fails on the first request answers with the reason.
-->

---

## Register It to Unity Catalog

```python
mlflow.set_registry_uri("databricks-uc")

logged = mlflow.pyfunc.log_model(
    name="agent",
    python_model="agent.py",             # models-from-code, not a pickle
    code_paths=["tools.py", "../Lab_3_Semantic_Search/data_utils.py"],
    model_config=MODEL_CONFIG,           # everything that is not a credential
    resources=RESOURCES,                 # everything the endpoint may reach
    pip_requirements=PIP_REQUIREMENTS,   # pinned, not inferred
    registered_model_name=UC_MODEL_NAME,
)
```

- **The agent becomes a versioned, governed artifact** in Unity Catalog, with a version number
- **`python_model="agent.py"` stores the source file.** What gets deployed is code you can read
- **Pin the requirements.** Inference reads the cluster, and a library with a local version segment resolves from no package index

<!--
Registration is what turns the agent from a notebook cell into a
governed object: it has a three-part Unity Catalog name, it has
versions, and access to it is a Unity Catalog grant like any table.

Models-from-code matters for review as well as for reliability.
The artifact contains agent.py and tools.py as source. A reviewer
can read exactly what will run. Nothing had to survive being
serialized.

The requirements point is a measured failure, not a style
preference. Inferred requirements read the environment the
notebook is running in. A cluster carrying the Lab 6 memory wheel
produces a requirement with a local version segment, which no
package index can resolve, and the container fails to build about
fifteen minutes after you stopped watching.
-->

---

## Resources: What the Endpoint May Reach

```python
[
    DatabricksGenieSpace(genie_agent_id=...),      # the space genie_node asks
    DatabricksSQLWarehouse(warehouse_id=...),      # where that SQL actually runs
    *[DatabricksTable(table_name=...) for ...],    # the gold tables the SQL reads
    DatabricksServingEndpoint(endpoint_name=...),  # the LLM
    DatabricksServingEndpoint(endpoint_name=...),  # the embedding model
]
```

**The trap: a Genie space grant is not a SQL warehouse grant.**

- A model logged with the space and not the warehouse **deploys cleanly and routes correctly**
- Then every sensor question comes back `is not authorized to use or monitor this SQL Endpoint`
- **Declaring a space grants the space, not what is underneath it.** Two resources, two grants

<!--
Four kinds of thing are on the list, and the list lives in
build_resources in agent.py rather than in a notebook cell,
because Lab 6 redeploys this endpoint and has to declare exactly
the same thing.

The warehouse omission is worth dwelling on because of how it
fails. It does not fail at deploy. It does not fail at routing.
The endpoint comes up healthy and answers graph and manual
questions correctly, and only the telemetry path is broken, with
an error naming a component the participant never explicitly
configured.

That failure mode is the argument for reviewing the resource list
as a list rather than testing one happy path and declaring
victory.
-->

---

## Credentials Are Not Resources

Aura is not a Databricks object. It cannot be declared or granted. It has to travel.

```python
{
    "NEO4J_URI":      "{{secrets/<scope>/neo4j-uri}}",
    "NEO4J_USERNAME": "{{secrets/<scope>/neo4j-username}}",
    "NEO4J_PASSWORD": "{{secrets/<scope>/neo4j-password}}",
}
```

- **`dbutils` does not exist in a serving container.** There is no notebook and no notebook user to read a scope
- **Credentials arrive as environment variables** bound to `{{secrets/<scope>/<key>}}` references
- **The control plane resolves them when the endpoint starts.** What is stored is the reference; what exists in the container is the value
- **The password is never in the notebook, never in MLflow, never in the endpoint's own configuration**

<!--
This is the second half of the split, and it is the half people
get wrong. Databricks resources are declared and granted.
Everything else is a credential, and credentials go in as
references.

The dbutils detail is the one to say out loud. Notebook 01 reads
the Aura password with dbutils.secrets.get. That call cannot exist
in the served agent, so agent.py reads os.environ instead. This is
not a refactor for tidiness. It is the reason agent.py exists as a
separate file at all.

For the reviewer: the environment block is safe to display. The
values in it are pointers. Reading the endpoint configuration
tells you which scope and which key, and tells you nothing about
the secret. Whoever creates the endpoint has to be able to read
that scope, and that is the permission to check.
-->

---

## Deploy, Then Wait

```python
mlflow.set_experiment(f"/Users/{CURRENT_USER}/{ENDPOINT_NAME}")

deployment = agents.deploy(
    UC_MODEL_NAME, MODEL_VERSION,
    endpoint_name=ENDPOINT_NAME,
    environment_vars=ENVIRONMENT_VARS,
    scale_to_zero=True,
)
```

- **`agents.deploy`** creates the endpoint, attaches the version, applies the environment block, and grants the declared resources
- **Set the experiment first.** That is what makes the deployed agent log its traces back to MLflow
- **A first deploy takes roughly sixteen minutes.** The call returns in under a minute and the endpoint is not ready
- **`scale_to_zero=True`** means the first question after a quiet period is slow. Not a failure

<!--
One call does four things, and the third and fourth are the ones
that matter for this deck: the environment block and the grants
are both applied here, from the two lists built earlier.

Setting the experiment before deploying is easy to skip and
expensive to skip. Without it the endpoint works and produces no
traces, which is a poor trade when the thing you most want to see
is which tool ran.

The notebook polls and prints where the deploy got to, so nobody
has to guess. If it never reaches READY, the reason is in the
build logs on the endpoint page, not in the notebook.
-->

---

## Scoring the Deployed Agent

Two things are worth scoring, and they fail for different reasons.

```python
results = mlflow.genai.evaluate(
    data=EVAL_PAIRS,
    predict_fn=predict_fn,                    # predict_fn IS the endpoint
    scorers=[routing, Correctness(), RelevanceToQuery()],
)
```

- **Routing is deterministic:** a plain Python function decorated with `@scorer`, comparing expected tools against the trace. No judge needed for something the trace already states
- **`Correctness`** judges the answer against the facts you said a good answer contains
- **`RelevanceToQuery`** catches the answer that is true and about something else
- **Low `Correctness` with `routing` at 1.0** is a prompt or data problem. **Low `routing`** is a supervisor problem

<!--
The reason to separate them is that the fix lives in a different
file. A routing failure sends you to the supervisor prompt. An
answer failure sends you to the tool, the schema, or the data.
One aggregate score hides which.

predict_fn calls the endpoint rather than a graph built in the
notebook, so what is being scored is the deployed model, with the
serving principal's permissions, not a copy running as you. That
distinction is the whole point of evaluating after deployment
rather than before.
-->

---

## The Names Are a Contract

```python
UC_MODEL_NAME = "databricks-neo4j-workshop.agents.fleet_ops_assistant"
AGENT_ENDPOINT_PREFIX = "fleet-ops-assistant"
```

- **Constants in `agent.py`**, not strings a participant types
- **Lab 6 redeploys *this* endpoint** with memory added, rather than standing up a second one. Renaming either breaks Lab 6
- **A registered model name is scoped to its catalog**, so it is the same for everyone
- **A serving endpoint name is unique across the account**, so it carries the participant's slug, taken from their secret scope so the two cannot disagree about who they are

<!--
This looks like a housekeeping slide and it is actually a design
one. The endpoint name is derived from the same secret scope name
the credentials come from, rather than derived a second time from
the user. Two derivations can drift; one cannot.

Serving endpoint names are limited to sixty-three characters and
the slug can be longer than that on its own, so it is truncated to
fit.

The practical instruction for the room: do not rename these. Lab 6
calls the same function with the same scope and expects the same
endpoint back, which is what makes a redeploy a redeploy.
-->

---

## Summary

- **The endpoint is its own identity.** Nothing it can reach is inherited from you
- **Resources are declared and granted.** Databricks objects, named at log time, in a file under version control
- **Credentials are referenced, not declared.** Secret scope references resolved at startup, because `dbutils` is gone
- **The model is source, not a pickle.** A reviewer can read what runs
- **Evaluate the endpoint, not a copy of it**, and score routing separately from answers
- **Next:** Lab 6 gives this same endpoint memory, in the same graph as the fleet

<!--
The three ideas to leave with: the split between resources and
credentials, the fact that a served model is readable source, and
scoring routing separately from answers.

Everything in this deck existed so that the agent could be handed
to somebody who is not you, and so that the person who has to
approve that hand-off can read the permission surface in one file
rather than reconstructing it from a workspace.
-->
