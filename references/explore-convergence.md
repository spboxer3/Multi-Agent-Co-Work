# Explore convergence playbook

## The common failure
Explorers often keep searching because each new clue suggests three more files. That produces a wide, low-confidence graph that the planner cannot lock.

## Converge when you have one causal path
You do **not** need every related file. You need enough to answer these questions with evidence:
- where does the behavior enter?
- what state or side effect leaves the subsystem?
- which shared consumers make the blast radius non-local?
- where would a deterministic test most likely fail if the hypothesis is wrong?

## Breadth control
When the search fan-out exceeds five new files in a single hop, prune aggressively:
1. keep files named on the direct call path
2. keep consumers that import or instantiate the changed symbol
3. keep one representative test surface per subsystem
4. drop speculative “might matter later” files

## Evidence quality ladder
Good evidence is ordered like this:
1. symbol + file + reason (`Foo.bar in x.py writes cache key used by y.py`)
2. file + reason
3. file name only
4. vague subsystem mention

Do not leave explore if most evidence is level 3 or 4.
