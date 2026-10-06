---
name: strength-follows-the-action
description: Improve a text that fails strength-follows-the-action.
tags:
- universe
- strength-follows-the-action
max_turns: 10
allowed_tools:
- Read
- Glob
- Grep
- Skill
---

Improve this definition text. Reply with the improved text only.

The whole set it belongs to:

1. core: Which crossing and departure time does the traveller want?
2. core: How many passengers and vehicles travel on the ticket?
3. core: Which reduced fare does the traveller qualify for?
4. situational: Which cabin is still free on the overnight crossing?
5. situational: Does the vehicle exceed the standard height for the car deck?

enablement: action: sell a same-day crossing ticket; actor: ferry ticket clerk; timing: before the departure gate closes
strength: core

Improve item 3 so it reads clearly within the set. Item 3:

Which reduced fare does the traveller qualify for?
