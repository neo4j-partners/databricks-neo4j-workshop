# Workshop Improvement Plan

## Core Goal

Our tagline promises attendees they'll build AI agents powered by knowledge graphs. When most of the session is spent on DBA work, there is a gap between expectations and experience. Every improvement below exists to close that gap: make the workshop feel like an AI agent build from the first minute, even while the necessary provisioning and data loading happens.

---

## Feedback Area 1: Lead with the Why

**The feedback:** The current intro moves straight to the architecture slide and into the lab. Attendees never hear why the problem matters or see what they are building before they start building it. The sequence should be: why this matters, then what you'll build, then how to build it. Right now we skip the first two.

**Suggested approaches:**

- Open with the Product Marketing narrative, not the architecture diagram. Frame the business problem first: fragmented aircraft data, sensor telemetry disconnected from maintenance history, questions no single database can answer.
- Add a 10 to 15 minute "why" segment before Lab 1 covering:
  - The pain: relationship-rich questions like "which aircraft share a component with a known failure" are painful in SQL alone.
  - The pattern: dual-database architecture where Neo4j owns relationships and Databricks owns telemetry at scale.
  - The payoff: a Supervisor Agent that answers natural language questions across both.
- Move the architecture slide to after the problem framing so it lands as the solution, not the starting point.
- Give attendees one memorable question the finished system can answer and repeat it at each lab transition: "by Lab 4, you'll ask this in plain English and get a real answer."

## Feedback Area 2: Preview the Prototype Early

**The feedback:** With provisioning and data loading constraints, it takes about 2.5 hours to reach the exciting part. Rather than fighting the setup time, show attendees the end state at the top. They will do the DBA work more willingly when they can see what they are working toward.

**Suggested approaches:**

- Run a 5 to 10 minute live demo of the finished Supervisor Agent in the first 15 minutes, using a fully provisioned instructor environment. Ask it 2 or 3 compelling questions that hit both the Genie space and the Neo4j MCP agent.
- Show the routing visibly: one question answered from Lakehouse telemetry via SQL, one from the graph via Cypher, one compound question that needs both. This makes the dual-database payoff concrete.
- Record a 2 to 3 minute backup video of the same demo in case of live-demo failure or for attendees who arrive late.
- Reframe each lab as a step toward the demo they already saw: "Lab 2 loads the data the agent just queried," "Lab 3 builds the semantic search the agent used." Add a one-line "where this fits" callout at the top of each lab.
- Where possible, pre-provision the slowest steps before the session starts. Any waiting that remains becomes discussion time: while data loads, walk through what the load is enabling rather than letting attendees idle.

## Feedback Area 3: Build a Real Call to Action into the Close

**The feedback:** The finish line should not be "cool, we built a thing." It should be attendees walking out ready to book a conversation with an AE or SE about their own use cases. Without a deliberate close, we run great demos that don't convert.

**Suggested approaches:**

- Replace the generic wrap-up with a structured 15 minute closing segment:
  - Map the workshop pattern to the industries in the room. Tailor 2 or 3 use case slides to the companies registered: supply chain, fraud, customer 360, equipment monitoring.
  - Show proof: 2 or 3 short customer stories where this architecture is delivering value in production, with concrete outcomes.
  - Make one clear ask: a specific next step, such as booking a scoping session with an AE or SE, with a QR code or sign-up link on the final slide.
- Prepare the tailored slides from the registration list before each event. Assign an owner for this so it happens every time.
- Have AEs and SEs in the room during the final lab so the handoff is a warm introduction, not a cold follow-up email.
- Add a lightweight exit survey with one qualifying question: "do you have a use case involving connected data you'd like to discuss?" Route yes responses to the account team within 48 hours.
- Track conversion: meetings booked per event becomes the success metric for the close, alongside lab completion rate.
