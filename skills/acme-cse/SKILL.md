---
name: acme-cse
license: BSD-3-Clause
metadata:
  authors:
    - name: Andreas Kraft
      orcid: https://orcid.org/0009-0007-5592-7195
      github: https://github.com/ankraft
description: >
  Answer questions about the ACME oneM2M CSE open source project — installation,
  configuration, runtime options, protocol bindings, plugins, scripting, and development.
  Use this skill whenever the user asks anything about ACME CSE, oneM2M, acmecse,
  acme.ini, CSE setup, or running/configuring the ACME middleware, even if the
  question seems simple. The skill provides structured fetch strategies and output
  templates to answer consistently and accurately from the live documentation.
---

# ACME oneM2M CSE Skill

## Overview

The **ACME CSE** is an open source Python implementation of the oneM2M IoT standard,
designed for education and small trials. It is installed via pip (`pip install acmecse`)
or by cloning the GitHub repo. All documentation lives at **https://acmecse.net** (MkDocs /
Material for MkDocs). The GitHub repo is **https://github.com/ankraft/ACME-oneM2M-CSE**.

Current release as of skill authoring: **v2026.05**. Always note if the user might be on
a different version, and suggest checking the site for the latest.

---

## Site Navigation Map

Use these URLs directly — do not guess or construct URLs.

### Top-level entry points

| Section | URL |
|---|---|
| Home / intro | https://acmecse.net/ |
| What is ACME CSE? | https://acmecse.net/home/ACME-CSE-introduction/ |
| What is oneM2M? | https://acmecse.net/home/oneM2M-introduction/ |
| Supported features | https://acmecse.net/home/Supported/ |
| Roadmap | https://acmecse.net/home/Roadmap/ |
| FAQ | https://acmecse.net/help/FAQ/ |

### Setup & Running

| Page | URL |
|---|---|
| Installation | https://acmecse.net/setup/Installation/ |
| Running | https://acmecse.net/setup/Running/ |
| Database Setup | https://acmecse.net/setup/Database/ |
| Certificates, Tokens & Auth | https://acmecse.net/setup/Certificates/ |

### Configuration (all under `setup/`)

| Page | URL |
|---|---|
| Introduction (INI format, Zookeeper, env vars, interpolation) | https://acmecse.net/setup/Configuration-introduction/ |
| Basic Configuration | https://acmecse.net/setup/Configuration-basic/ |
| CSE General Settings | https://acmecse.net/setup/Configuration-cse/ |
| CSE Registrations | https://acmecse.net/setup/Configuration-registrations/ |
| Databases | https://acmecse.net/setup/Configuration-database/ |
| Logging | https://acmecse.net/setup/Configuration-logging/ |
| Protocol Binding — CoAP | https://acmecse.net/setup/Configuration-coap/ |
| Protocol Binding — HTTP | https://acmecse.net/setup/Configuration-http/ |
| Protocol Binding — MQTT | https://acmecse.net/setup/Configuration-mqtt/ |
| Protocol Binding — WebSocket | https://acmecse.net/setup/Configuration-ws/ |
| Scripting | https://acmecse.net/setup/Configuration-scripting/ |
| User Interfaces | https://acmecse.net/setup/Configuration-uis/ |
| oneM2M Resources | https://acmecse.net/setup/Configuration-resources/ |

### Operation

| Page | URL |
|---|---|
| Infrastructure Diagrams | https://acmecse.net/setup/Operation-diagrams/ |
| CSE Management API | https://acmecse.net/setup/Operation-management/ |
| MQTT Broker | https://acmecse.net/setup/Operation-mqtt/ |
| Upper Tester | https://acmecse.net/setup/Operation-uppertester/ |

### User Interfaces

| Page | URL |
|---|---|
| Console UI | https://acmecse.net/setup/Console/ |
| Text UI | https://acmecse.net/setup/TextUI/ |
| Web UI | https://acmecse.net/setup/WebUI/ |

### Development

| Page | URL |
|---|---|
| Architecture Overview | https://acmecse.net/development/Overview/ |
| API Docs (pointer to api.acmecse.net) | https://acmecse.net/development/APIDocs/ |
| Event System | https://acmecse.net/development/EventSystem/ |
| Unit Tests | https://acmecse.net/development/UnitTests/ |
| Start-Up Resources | https://acmecse.net/development/StartupResources/ |
| Attribute Policies | https://acmecse.net/development/AttributePolicies/ |
| FlexContainer Policies | https://acmecse.net/development/FlexContainerPolicies/ |
| Resource Type Policies | https://acmecse.net/development/ResourceTypePolicies/ |
| Help File Format | https://acmecse.net/development/HelpDocumentation/ |
| ACMEScript Introduction | https://acmecse.net/development/ACMEScript/ |
| ACMEScript Loading & Running | https://acmecse.net/development/ACMEScript-loading/ |
| ACMEScript Operations | https://acmecse.net/development/ACMEScript-operations/ |
| ACMEScript Functions | https://acmecse.net/development/ACMEScript-functions/ |
| ACMEScript Variables | https://acmecse.net/development/ACMEScript-variables/ |
| ACMEScript Meta Tags | https://acmecse.net/development/ACMEScript-metatags/ |
| ACMEScript Upper Tester Integration | https://acmecse.net/development/ACMEScript-uppertester/ |
| Embedding ACME CSE | https://acmecse.net/development/Embedding_ACME/ |
| Debug Mode | https://acmecse.net/development/DebugMode/ |
| Type Checking | https://acmecse.net/development/TypeChecking/ |
| Third Party Components | https://acmecse.net/development/ThirdPartyLibraries/ |
| Notification Server tool | https://acmecse.net/development/tools/NotificationServer/ |
| Onboarding Tool | https://acmecse.net/development/tools/OnboardingTool/ |
| Zookeeper Tool | https://acmecse.net/development/tools/ZookeeperTool/ |
| Hashing Credentials | https://acmecse.net/development/tools/HashCredentials/ |

### Internal API Documentation (api.acmecse.net)

The internal Python API is documented at **https://api.acmecse.net** (generated by pydoctor).
Use `web_fetch` on specific class/module URLs for detailed API questions. Key entry points:

| Module/Package | URL |
|---|---|
| Index | https://api.acmecse.net/index.html |
| Module index | https://api.acmecse.net/moduleIndex.html |
| Class index | https://api.acmecse.net/classIndex.html |
| acme.helpers (EventManager etc.) | https://api.acmecse.net/acme.helpers.html |
| acme.runtime (PluginManager etc.) | https://api.acmecse.net/acme.runtime.html |
| acme.plugins | https://api.acmecse.net/acme.plugins.html |
| acme.resources | https://api.acmecse.net/acme.resources.html |
| acme.services | https://api.acmecse.net/acme.services.html |

### Plugins & HowTos

| Page | URL |
|---|---|
| Plugins Overview | https://acmecse.net/plugins/PluginsOverview/ |
| Plugin API & Lifecycle | https://acmecse.net/plugins/PluginAPI/ |
| Plugin Manager | https://acmecse.net/plugins/PluginManager/ |
| Service Plugins | https://acmecse.net/plugins/PluginServicePlugins/ |
| Developing an Example Plugin | https://acmecse.net/plugins/PluginExample/ |
| CSE Core Plugins | https://acmecse.net/plugins/PluginCorePlugins/ |
| HowTos Index | https://acmecse.net/howtos/HowTos/ |

---

## Fetch Strategy by Question Type

Always use `web_fetch` to retrieve the relevant page before answering. Pick the
**most specific** page; fetch multiple pages only if the question spans sections.

| Question type | Pages to fetch |
|---|---|
| Install, first run, pip vs git | Installation |
| Start/stop, CLI flags | Running |
| Any `acme.ini` setting | Configuration-introduction + the relevant `Configuration-*` page |
| HTTP / HTTPS / TLS / CORS / WSGI | Configuration-http |
| MQTT setup or broker | Configuration-mqtt + Operation-mqtt |
| CoAP | Configuration-coap |
| WebSocket | Configuration-ws |
| Database, TinyDB, PostgreSQL | Configuration-database + Database Setup |
| Logging, log levels | Configuration-logging |
| Authentication, certificates | Certificates + Configuration-http (security section) |
| CSE-ID, CSE type, registrations | Configuration-cse + Configuration-registrations |
| Scripting, ACMEScript | Configuration-scripting + ACMEScript Introduction |
| Console / Text / Web UI | Configuration-uis + the relevant UI page |
| Plugin development, lifecycle, API | Plugins Overview + Plugin API & Lifecycle |
| Plugin manager, dependency injection | Plugin Manager |
| Service plugins | Service Plugins |
| Plugin example / tutorial | Developing an Example Plugin |
| Core/built-in plugins | CSE Core Plugins |
| Event system, event handlers, custom events | Event System |
| Internal Python API, class/module reference | development/APIDocs + fetch specific page from api.acmecse.net |
| Architecture, internals, embedding | development/Overview + Embedding_ACME |
| oneM2M concepts, terminology | home/oneM2M-introduction/ + home/Supported/ |
| Docker | HowTos (search for Docker howto) |
| Zookeeper config | Configuration-introduction + tools/ZookeeperTool |
| Environment variables / secrets | Configuration-introduction (env vars section) |

---

## Configuration Page Structure

Every `Configuration-*` page follows a consistent pattern. When parsing:

1. **Section header** — INI section name in backticks, e.g. `[http]`, `[http.security]`
2. **Settings table** — columns: `Setting | Description | Default`
3. **Default values** often reference `${basic.config:*}` interpolation variables —
   fetch `Configuration-basic` to resolve them if needed.
4. **Cross-references** to related pages are in "See also" callouts.

### Key configuration facts to always include in answers

- Config is INI format; only settings that differ from defaults need to be in `acme.ini`.
- The default file is `acme.ini.default` (do not edit it); user file is `acme.ini`.
- Settings interpolation uses `${section:key}` syntax.
- Environment variables can be used with the same `${}` syntax.
- A `.env` file in the base directory (or parents) is auto-loaded.
- Zookeeper is an alternative to file-based config for distributed setups.
- Dot notation (`section.key`) is used for runtime access from ACMEScript.

---

## Running / CLI Facts

Two invocation styles — always show both when relevant:

| Installation type | Command |
|---|---|
| pip package | `acmecse` |
| Manual / git clone | `python3 -m acme` |

Key CLI flags (fetch `Running` page for the full table):
- `--config <file>` — alternate config file
- `-dir <directory>` — alternate base directory
- `--db-reset` — wipe database on start
- `--headless` — no console UI, minimal output
- `--http` / `--https` — override TLS setting
- `--http-wsgi` — enable WSGI server
- `--log-level` — override log level
- `--textui` — start with Text UI
- `@argsfile.txt` — read arguments from a file

Stop the CSE: press **Q** (uppercase) or **Ctrl-C once**. Warn the user that double
Ctrl-C can cause data corruption.

---

## Output Templates

### Template A — Installation / Setup Answer

```
## Installation

**Requirements:** Python 3.11 or newer (Python 3.13 recommended; 3.14 not yet tested).

**Quickstart (pip):**
```
python -m pip install acmecse
acmecse
```

**Manual (git clone):**
```
git clone https://github.com/ankraft/ACME-oneM2M-CSE.git
cd ACME-oneM2M-CSE
python3 -m pip install -r requirements.txt
python3 -m acme
```

On first run with no config file, an interactive onboarding wizard starts and
creates `acme.ini`. Reference: https://acmecse.net/setup/Installation/
```

### Template B — Configuration Setting Answer

Always include:
1. **INI section** (e.g. `[http]`)
2. **Setting name** and what it controls
3. **Default value**
4. **Minimal snippet** showing only the changed setting
5. **Link** to the documentation page

Example format:
```
**Section:** `[http]`
**Setting:** `port`
**Default:** `8080` (from `${basic.config:httpPort}`)

To change the HTTP port to 9000, add to `acme.ini`:
```ini
[http]
port = 9000
```

Docs: https://acmecse.net/setup/Configuration-http/
```

### Template C — Troubleshooting / How-To Answer

1. State what the user is trying to achieve
2. Identify the relevant config section(s) and CLI flags
3. Provide a minimal working `acme.ini` snippet
4. Note any security warnings (the docs use Warning/Attention callouts — reproduce them)
5. Link to the docs page

---

## Important Domain Vocabulary

| Term | Meaning |
|---|---|
| CSE | Common Services Entity — the oneM2M server/middleware node |
| IN-CSE | Infrastructure Node CSE (cloud/backend) |
| MN-CSE | Middle Node CSE (gateway) |
| ASN-CSE | Application Service Node CSE (edge device) |
| AE | Application Entity — a client application |
| CSE-ID | Unique identifier for a CSE instance, e.g. `/id-in` |
| originator | The entity making a request (AE or CSE) |
| registrar CSE | A parent/upstream CSE that this CSE registers with |
| TinyDB | Default embedded JSON database (dev/small deployments) |
| WSGI | Production-grade HTTP server mode (waitress-based, no TLS) |
| ACMEScript | Built-in scripting language for automation and testing |
| Upper Tester | oneM2M TS-0019 testing interface (enable only for testing) |

---

## Security Warnings to Always Reproduce

If the user's question touches any of these, reproduce the warning verbatim:

- `enableManagementEndpoint = True` → **may expose sensitive info and risk total data loss**
- `enableStructureEndpoint = True` → **exposes potentially sensitive information**
- `enableUpperTesterEndpoint = True` → **may lead to total data loss**
- `allowPatchForDelete = True` → **non-standard, not part of oneM2M HTTP binding spec**
- `--db-reset` → **wipes the database on every start**
- Double Ctrl-C to stop → **may cause data corruption**
- `.env` file → **do not commit to version control**
- `acme.ini.default` → **do not edit; copy settings to `acme.ini` instead**

---

## Versioning Note

The docs reflect the current release. If the user mentions a specific version or
asks about changelog/roadmap items, fetch https://acmecse.net/home/Roadmap/ and
check the GitHub releases page at https://github.com/ankraft/ACME-oneM2M-CSE/releases.
