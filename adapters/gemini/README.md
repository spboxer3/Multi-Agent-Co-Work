# Gemini adapter

Gemini CLI supports extensions, slash commands, skills, and long-term memory in `GEMINI.md`. This package ships an extension with command wrappers that call the repository-local runtime.

The Claude Code plugin colon syntax (`/plugin:command`) does not apply to Gemini. Gemini uses its own extension format, and the adapter wrappers are registered through the Gemini extension system rather than as slash-command plugins.

Refer to the extension manifest in this directory for the list of registered commands and their mappings to the multi-agent-cowork runtime.
