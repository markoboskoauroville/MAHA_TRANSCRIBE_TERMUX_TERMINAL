# LESSONS

## 5.10.2026
- **Never write a provider's model name as the truth.** AssemblyAI bumps the version inside the name
  (universal-3-pro → universal-3-5-pro) and retires the old field (speech_model → speech_models). Ask the
  API: an invalid name in `speech_models` returns the full valid list as a free 400. Store the choice as a
  family (version digits replaced by #) and resolve it to the newest member at send time.
- **Omitting `speech_models` is AssemblyAI's own best default**, which is always current.
- **werkzeug's listening socket survives `os.execv`.** Without `os.closerange(3, …)` before the exec, the
  old port stays open with no one answering and portpick moves the new server up one port.
