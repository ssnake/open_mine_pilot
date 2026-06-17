3. Event Timeouts
- if an expected asynchronous event takes longer than 60 seconds, you will receive `[SYSTEM EVENT: state_timeout]`
- if you receive a timeout, you should evaluate your current situation and retry the action, try a different action, or report the issue to the user.
