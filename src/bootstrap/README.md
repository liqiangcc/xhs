# Bootstrap / Composition Root

This is the only area allowed to know both concrete Infrastructure adapters and Application construction.

Composition-root responsibilities:
- create concrete adapters;
- inject them into Application use cases;
- assemble inbound Interfaces;
- keep dependency wiring out of Domain and Application.

No concrete adapter is wired yet because Phase A intentionally does not migrate production behavior. Wiring will be added with the first vertical use-case slice.
