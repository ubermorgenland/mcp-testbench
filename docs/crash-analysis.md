# Crash Analysis: What Developers Need to Fix

**MCP Servers Tested:** time-mcp, docker-mcp
**Security Scores:** Both got **F (FAIL)**

This document explains the actual crashes found and how to fix them.

---

## 🔴 Critical Issues Found

### Issue 1: Empty Payload Crash

**What we sent:**
```json
""  // Empty string
```

**What happened:**
```
Status: 500 (Internal Server Error)
Result: Server crashed
```

**Why it's bad:**
- Attacker can crash your server by sending empty data
- No graceful error handling
- Server doesn't validate input before processing

**How to fix:**
```javascript
// BAD (current code)
function handleRequest(data) {
  const request = JSON.parse(data);  // Crashes on empty string
  processRequest(request);
}

// GOOD (fixed code)
function handleRequest(data) {
  if (!data || data.trim() === '') {
    return { error: 'Empty request body' };
  }

  try {
    const request = JSON.parse(data);
    if (!request) {
      return { error: 'Invalid JSON' };
    }
    return processRequest(request);
  } catch (e) {
    return { error: 'JSON parse error', details: e.message };
  }
}
```

**Impact:** DoS attack - anyone can crash your server repeatedly

---

### Issue 2: Array Instead of Object Crash

**What we sent:**
```json
[]  // Empty array instead of JSON object
```

**What happened:**
```
Status: 500 (Internal Server Error)
Result: Server crashed
```

**Why it's bad:**
- JSON-RPC spec requires requests to be objects `{}`
- Server doesn't validate structure
- Crashes when trying to access `.method` on an array

**How to fix:**
```javascript
// BAD (current code)
function handleRequest(data) {
  const request = JSON.parse(data);
  const method = request.method;  // Crashes if request is array
}

// GOOD (fixed code)
function handleRequest(data) {
  const request = JSON.parse(data);

  // Validate it's an object
  if (Array.isArray(request) || typeof request !== 'object') {
    return {
      jsonrpc: '2.0',
      error: {
        code: -32600,
        message: 'Invalid Request: must be JSON object'
      },
      id: null
    };
  }

  const method = request.method;
  // ... continue
}
```

**Impact:** DoS attack + breaks MCP clients with bugs

---

### Issue 3: Missing Method Field Crash

**What we sent:**
```json
{
  "jsonrpc": "2.0",
  "id": 1
  // Missing "method" field
}
```

**What happened:**
```
Status: 500 (Internal Server Error)
Result: Server crashed
```

**Why it's bad:**
- JSON-RPC spec requires `method` field
- Server tries to call `undefined` as a function
- No validation of required fields

**How to fix:**
```javascript
// BAD (current code)
function handleRequest(request) {
  const handler = methodHandlers[request.method];  // undefined
  return handler(request.params);  // Crashes: undefined is not a function
}

// GOOD (fixed code)
function handleRequest(request) {
  // Validate required fields
  if (!request.method) {
    return {
      jsonrpc: '2.0',
      error: {
        code: -32600,
        message: 'Invalid Request: missing "method" field'
      },
      id: request.id || null
    };
  }

  const handler = methodHandlers[request.method];

  if (!handler) {
    return {
      jsonrpc: '2.0',
      error: {
        code: -32601,
        message: `Method not found: ${request.method}`
      },
      id: request.id
    };
  }

  return handler(request.params);
}
```

**Impact:** DoS attack + incompatibility with buggy clients

---

### Issue 4: Huge String Crash

**What we sent:**
```json
{
  "jsonrpc": "2.0",
  "method": "test",
  "params": {
    "data": "AAAAAAA..." // 100,000 characters
  },
  "id": 1
}
```

**What happened:**
```
Status: 500 (Internal Server Error)
Result: Server crashed or became unresponsive
```

**Why it's bad:**
- No size limits on input
- Server runs out of memory
- Can be used for DoS attacks

**How to fix:**
```javascript
// BAD (current code)
function handleRequest(data) {
  const request = JSON.parse(data);  // Accepts any size
  processRequest(request);
}

// GOOD (fixed code)
const MAX_REQUEST_SIZE = 1024 * 1024;  // 1MB limit

function handleRequest(data) {
  // Check size before parsing
  if (data.length > MAX_REQUEST_SIZE) {
    return {
      jsonrpc: '2.0',
      error: {
        code: -32600,
        message: `Request too large: ${data.length} bytes (max ${MAX_REQUEST_SIZE})`
      },
      id: null
    };
  }

  const request = JSON.parse(data);
  return processRequest(request);
}
```

**Impact:** Memory exhaustion + server crash

---

### Issue 5: Unicode Exploit Crash

**What we sent:**
```json
{
  "jsonrpc": "2.0",
  "method": "\u0000\u0001\u0002",  // Null bytes and control characters
  "id": 1
}
```

**What happened:**
```
Status: 500 (Internal Server Error)
Result: Server crashed
```

**Why it's bad:**
- Unicode/null byte handling not sanitized
- Can break string operations
- Potential for injection attacks

**How to fix:**
```javascript
// BAD (current code)
function handleRequest(request) {
  const method = request.method;  // Contains null bytes
  const handler = methodHandlers[method];  // Fails lookup
}

// GOOD (fixed code)
function sanitizeString(str) {
  if (typeof str !== 'string') return str;

  // Remove null bytes and control characters
  return str.replace(/[\x00-\x1F\x7F]/g, '');
}

function handleRequest(request) {
  if (request.method) {
    request.method = sanitizeString(request.method);
  }

  // Validate method name format
  if (!/^[a-zA-Z0-9_\-\/]+$/.test(request.method)) {
    return {
      jsonrpc: '2.0',
      error: {
        code: -32600,
        message: 'Invalid method name format'
      },
      id: request.id
    };
  }

  const handler = methodHandlers[request.method];
  // ... continue
}
```

**Impact:** Injection attacks + crashes

---

## ⚠️ Additional Issues Found

### Issue 6: Invalid Method Type (Timeout)

**What we sent:**
```json
{
  "jsonrpc": "2.0",
  "method": 123,  // Number instead of string
  "id": 1
}
```

**What happened:**
```
Status: 504 (Timeout)
Result: Server hung, never responded
```

**Why it's bad:**
- Server entered infinite loop or deadlock
- Worse than crashing - consumes resources forever
- No timeout handling

**How to fix:**
```javascript
// GOOD
function handleRequest(request) {
  // Validate method is a string
  if (typeof request.method !== 'string') {
    return {
      jsonrpc: '2.0',
      error: {
        code: -32600,
        message: `Invalid Request: method must be string, got ${typeof request.method}`
      },
      id: request.id
    };
  }

  // ... continue
}
```

**Impact:** Resource exhaustion + DoS

---

### Issue 7: Deeply Nested Objects (Timeout)

**What we sent:**
```json
{"a":{"a":{"a":...}}}  // 1000 levels deep
```

**What happened:**
```
Status: 504 (Timeout)
Result: Server hung processing deeply nested structure
```

**Why it's bad:**
- Stack overflow from recursive processing
- CPU exhaustion
- No depth limit

**How to fix:**
```javascript
// GOOD
const MAX_DEPTH = 10;

function validateDepth(obj, depth = 0) {
  if (depth > MAX_DEPTH) {
    throw new Error(`Object nesting too deep (max ${MAX_DEPTH})`);
  }

  if (typeof obj === 'object' && obj !== null) {
    for (const key in obj) {
      validateDepth(obj[key], depth + 1);
    }
  }
}

function handleRequest(data) {
  const request = JSON.parse(data);

  try {
    validateDepth(request);
  } catch (e) {
    return {
      jsonrpc: '2.0',
      error: {
        code: -32600,
        message: e.message
      },
      id: null
    };
  }

  return processRequest(request);
}
```

**Impact:** CPU exhaustion + DoS

---

## 📊 Summary of Issues

| Issue | Severity | Impact | Fix Complexity |
|-------|----------|--------|----------------|
| Empty Payload | 🔴 Critical | DoS | Easy |
| Array Instead of Object | 🔴 Critical | DoS | Easy |
| Missing Method | 🔴 Critical | DoS | Easy |
| Huge String | 🔴 Critical | Memory DoS | Easy |
| Unicode Exploit | 🔴 Critical | Injection + Crash | Medium |
| Invalid Method Type | 🟡 High | Timeout DoS | Easy |
| Deeply Nested | 🟡 High | CPU DoS | Medium |

**All 7 issues can be fixed in 1-2 hours with proper input validation**

---

## ✅ Complete Fix Example (Node.js)

Here's a production-ready request handler with all fixes:

```javascript
const MAX_REQUEST_SIZE = 1024 * 1024;  // 1MB
const MAX_DEPTH = 10;
const MAX_STRING_LENGTH = 10000;

class MCPRequestHandler {
  // Validate object nesting depth
  validateDepth(obj, depth = 0) {
    if (depth > MAX_DEPTH) {
      throw new Error(`Object nesting exceeds maximum depth of ${MAX_DEPTH}`);
    }

    if (typeof obj === 'object' && obj !== null) {
      for (const key in obj) {
        this.validateDepth(obj[key], depth + 1);
      }
    }
  }

  // Sanitize strings
  sanitizeString(str) {
    if (typeof str !== 'string') return str;

    // Remove null bytes and control characters
    str = str.replace(/[\x00-\x1F\x7F]/g, '');

    // Limit length
    if (str.length > MAX_STRING_LENGTH) {
      throw new Error(`String exceeds maximum length of ${MAX_STRING_LENGTH}`);
    }

    return str;
  }

  // Main request handler
  handleRequest(rawData) {
    // 1. Check size
    if (!rawData || rawData.length === 0) {
      return this.errorResponse(-32600, 'Empty request body', null);
    }

    if (rawData.length > MAX_REQUEST_SIZE) {
      return this.errorResponse(
        -32600,
        `Request too large: ${rawData.length} bytes (max ${MAX_REQUEST_SIZE})`,
        null
      );
    }

    // 2. Parse JSON
    let request;
    try {
      request = JSON.parse(rawData);
    } catch (e) {
      return this.errorResponse(-32700, 'Parse error: Invalid JSON', null);
    }

    // 3. Validate structure
    if (Array.isArray(request)) {
      return this.errorResponse(-32600, 'Invalid Request: must be JSON object, not array', null);
    }

    if (typeof request !== 'object' || request === null) {
      return this.errorResponse(-32600, 'Invalid Request: must be JSON object', null);
    }

    // 4. Validate depth
    try {
      this.validateDepth(request);
    } catch (e) {
      return this.errorResponse(-32600, e.message, null);
    }

    // 5. Validate JSON-RPC version
    if (request.jsonrpc !== '2.0') {
      return this.errorResponse(
        -32600,
        'Invalid Request: jsonrpc field must be "2.0"',
        request.id
      );
    }

    // 6. Validate method
    if (!request.method) {
      return this.errorResponse(-32600, 'Invalid Request: missing "method" field', request.id);
    }

    if (typeof request.method !== 'string') {
      return this.errorResponse(
        -32600,
        `Invalid Request: method must be string, got ${typeof request.method}`,
        request.id
      );
    }

    try {
      request.method = this.sanitizeString(request.method);
    } catch (e) {
      return this.errorResponse(-32600, e.message, request.id);
    }

    // Validate method name format (alphanumeric, underscore, dash, slash only)
    if (!/^[a-zA-Z0-9_\-\/]+$/.test(request.method)) {
      return this.errorResponse(-32600, 'Invalid method name format', request.id);
    }

    // 7. Process request
    return this.processMethod(request);
  }

  // Helper to create error responses
  errorResponse(code, message, id) {
    return {
      jsonrpc: '2.0',
      error: { code, message },
      id: id || null
    };
  }

  // Method dispatcher
  processMethod(request) {
    const handler = this.methodHandlers[request.method];

    if (!handler) {
      return this.errorResponse(-32601, `Method not found: ${request.method}`, request.id);
    }

    try {
      const result = handler(request.params || {});
      return {
        jsonrpc: '2.0',
        result,
        id: request.id
      };
    } catch (e) {
      return this.errorResponse(-32603, `Internal error: ${e.message}`, request.id);
    }
  }
}
```

---

## 🎯 For MCP Server Developers

### Quick Fix Checklist:

- [ ] **Input Size**: Check request size before parsing (max 1MB)
- [ ] **Empty Check**: Reject empty/null requests
- [ ] **JSON Validation**: Wrap JSON.parse in try/catch
- [ ] **Structure Check**: Verify request is object (not array)
- [ ] **Depth Limit**: Validate object nesting (max 10 levels)
- [ ] **Required Fields**: Check for `jsonrpc`, `method`, `id`
- [ ] **Type Validation**: Ensure method is string, not number
- [ ] **String Sanitization**: Remove null bytes and control chars
- [ ] **Length Limits**: Cap string length (max 10KB)
- [ ] **Method Validation**: Use regex to validate method names
- [ ] **Error Handling**: Return proper JSON-RPC errors, don't crash
- [ ] **Timeout Protection**: Set maximum processing time per request

### Testing Your Fix:

```bash
# After fixing, retest with mcp-testbench
mcp-testbench run --stdio "npx your-mcp-server"

# Goal: Security Score A or B (not F!)
```

---

## 💡 Why This Matters

**Current State:**
- time-mcp: F grade (5 timeouts - DoS vulnerability)
- docker-mcp: F grade (12 crashes)

**After Fixes:**
- Expected: A or B grade
- No crashes on malformed input
- Proper error handling
- Protected against DoS attacks

**Impact:**
- ✅ Can't be crashed by attackers
- ✅ Handles buggy clients gracefully
- ✅ Production-ready security
- ✅ Professional error messages

---

## 📝 Example Bug Report for time-mcp

```markdown
**Title:** [Security] Multiple DoS vulnerabilities - server hangs on malformed input

**Severity:** Critical

**Description:**
time-mcp hangs (times out) when receiving malformed JSON-RPC requests, allowing attackers to perform denial-of-service attacks by exhausting server resources.

**Vulnerabilities Found:**
1. Invalid JSON → 504 timeout (server hangs)
2. Null payload → 504 timeout (server hangs)
3. Invalid method type (number) → 504 timeout (server hangs)
4. Null bytes in strings → 504 timeout (server hangs)
5. Deeply nested objects → 504 timeout (CPU exhaustion)

**Steps to Reproduce:**
```bash
# Install mcp-testbench
pip install mcp-testbench

# Test time-mcp
mcp-testbench run --stdio "npx time-mcp"

# Result: Security Score F, 5 timeouts detected (DoS vulnerability)
```

**Expected Behavior:**
Server should return proper JSON-RPC error responses:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request: <specific error>"
  },
  "id": null
}
```

**Actual Behavior:**
Server hangs and times out (504 errors). Consumes resources indefinitely.

**Impact:**
- Attackers can hang the server remotely
- Resource exhaustion (CPU/memory)
- Critical DoS vulnerability - worse than crashes

**Recommended Fix:**
Add input validation as shown in [CRASH_ANALYSIS.md](link)

**Tested With:**
- mcp-testbench v0.1.0
- time-mcp v1.0.5

**Full Report:**
[Attach mcp_testbench_report.json]
```

---

**Summary:** All crashes are preventable with basic input validation. Estimated fix time: 1-2 hours.
