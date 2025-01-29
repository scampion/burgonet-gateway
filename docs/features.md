## Audit log


Each exchange with the gateway is logged in a structured format. The logs are written to the standard output and can be redirected to a file or a log collector.
Here is an example of a log entry:

```txt
2025-01-28T15:05:14.454037+01:00 INFO audit - df7f3c96-a4f6-4382-8a8a-b36ff13978bb User Some("alice") accessed location /ollama/gemma2/2b/
2025-01-28T15:05:14.454818+01:00 INFO audit - df7f3c96-a4f6-4382-8a8a-b36ff13978bb Request ### {  "model": "gemma2:2b-instruct-q6_K",                                     >
2025-01-28T15:05:14.962724+01:00 INFO audit - df7f3c96-a4f6-4382-8a8a-b36ff13978bb Response ### {"created_at":"2025-01-28T14:05:14.960232Z","done":true,"done_reason":"sto>
```
