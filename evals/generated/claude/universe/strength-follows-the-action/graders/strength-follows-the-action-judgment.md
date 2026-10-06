---
type: llm
focus: last_message
---

The reply is a new version of item 3 in this set:

1. core: Which crossing and departure time does the traveller want?
2. core: How many passengers and vehicles travel on the ticket?
3. core: Which reduced fare does the traveller qualify for?
4. situational: Which cabin is still free on the overnight crossing?
5. situational: Does the vehicle exceed the standard height for the car deck?

enablement: action: sell a same-day crossing ticket; actor: ferry ticket clerk; timing: before the departure gate closes
strength: core

PASS if, reading the artifact's enablement and its listed elements, a reader sees at once what this element contributes to the action and that the action needs it every time when it is core, or can go ahead without it in some situations when it is situational. A core element with a stated condition is judged as core only when that condition holds.
FAIL if this element is core but the action can plainly be taken without it in some situations, if it is situational but the action plainly cannot be taken without it, or if a reader cannot tell from its question what it contributes to the action; the critique says which.
