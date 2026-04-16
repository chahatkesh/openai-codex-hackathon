 # Full pipeline

  ## Phase 1: Vibecoder asks Codex to build something

  Example prompt:

  > “Build me an app that scrapes Product Hunt and sends me an SMS after 3 hours.”

  At this point, UFC is helping the user build an app.

  ———

  ## Phase 2: UFC checks FuseKit through MCP

  UFC connects to FuseKit MCP and asks:

  - what capabilities already exist?
  - are Product Hunt scraping and SMS sending already supported?
  - if yes, what are the runtime HTTP endpoints/contracts for using them in the deployed app?

  FuseKit MCP returns:

  - available capabilities
  - tool metadata
  - endpoint manifests / integration instructions
  - possibly markdown docs for UFC to understand usage

  So MCP is acting like:

  - capability discovery plane
  - integration-control plane
  - build-time guidance plane

  ———

  ## Phase 3: If capability is missing, UFC requests integration

  If UFC does not find a required capability, it calls a FuseKit MCP tool like:

  - request_integration

  with something like:

  - capability description
  - preferred tool name
  - optional docs URL

  FuseKit platform then:

  1. creates an integration job in DB
  2. forwards the job to the integrator pipeline
  3. returns a job ID and status back to UFC

  ———

  ## Phase 4: FuseKit integration pipeline runs on backend

  Now your backend runs the integration pipeline.

  ### Step 4.1 Discovery

  FuseKit agents inspect docs/search results and identify:

  - provider
  - auth model
  - endpoints
  - request/response structure

  ### Step 4.2 Reader

  They normalize docs into a structured capability spec.

  ### Step 4.3 Codegen

  They generate:

  - server-side execution code
  - internal capability metadata
  - HTTP execution contract
  - endpoint definitions
  - structured manifest
  - optional markdown docs for UFC/humans

  ### Step 4.4 Test/Fix

  They validate and repair the generated code.

  ### Step 4.5 Publish

  FuseKit publishes:

  - capability metadata to DB
  - runtime artifact to durable storage
  - HTTP endpoint registration
  - manifest/docs artifact to S3/DB/repo

  ———

  ## Phase 5: Credential check decides whether capability is live

  After code is generated, FuseKit checks whether provider credentials exist.

  ### If credentials exist

  Capability becomes:

  - live

  ### If credentials do not exist

  Capability becomes:

  - pending_credentials

  Then one of two things happens:

  - user adds their own credentials
  - FuseKit admin adds centralized credentials

  Once credentials are available:

  - capability moves to live

  This is critical:
  generated != executable
  until credentials are present.

  ———

  ## Phase 6: UFC receives endpoint contract and builds the app

  Once the capability exists, UFC gets back from MCP:

  - capability name
  - HTTP endpoint(s) to call
  - auth format
  - request schema
  - response schema
  - example payloads
  - optional markdown explanation

  Then UFC writes the deployed app.

  For example, UFC might generate:

  - a cron/scheduler
  - a backend job
  - a workflow runner
  - a Next.js/Node/Python app

  That app will later call FuseKit HTTP endpoints directly.

  ———

  ## Phase 7: The deployed app runs later

  Three hours later, the user’s deployed app executes.

  Example runtime flow:

  1. app calls FuseKit HTTP endpoint for Product Hunt fetch
  2. FuseKit executes Product Hunt integration
  3. FuseKit returns structured result
  4. app processes that result
  5. app calls FuseKit HTTP endpoint for SMS send
  6. FuseKit executes Twilio/SMS integration
  7. FuseKit returns success/failure

  At runtime, the deployed app is talking to FuseKit HTTP APIs, not MCP.

  ———

  # Wallet deduction flow

  This is the billing path you asked about.

  ## Rule

  Wallet deduction happens when the deployed app makes a real HTTP execution request to FuseKit.

  Not when:

  - UFC is only discovering tools
  - docs are being read
  - manifests are being returned
  - a capability is merely listed

  It should happen when:

  - FuseKit actually executes a billable capability

  ———

  ## Example runtime billing flow

  Suppose the app calls:

  - POST /execute/get_producthunt
  - POST /execute/send_sms

  ### Request 1: Product Hunt fetch

  1. app sends HTTP request to FuseKit
  2. FuseKit authenticates app/user/project
  3. FuseKit checks wallet balance
  4. FuseKit checks cost of get_producthunt
  5. if balance is sufficient:
      - deduct credits atomically
      - execute provider call
      - log execution
      - return result
  6. if execution fails in a refund-worthy way:
      - refund credits according to policy

  ### Request 2: SMS send

  Same flow:

  1. authenticate
  2. check wallet
  3. deduct cost
  4. execute SMS provider call
  5. log result
  6. refund if needed

  So the deployed app’s user is charged per actual endpoint execution.

  ———

  ## Who is paying?

  This depends on product design, but the clean model is:

  - the vibecoder owns a FuseKit wallet/project
  - the deployed app uses a FuseKit app token or project token
  - every HTTP execution is attributed to that vibecoder/project wallet

  So even if the app has many end users, the billing can still roll up to:

  - that user’s FuseKit account
  - or a specific project wallet

  ———

  ## Runtime request lifecycle for billing

  For every HTTP execution request:

  1. authenticate caller
  2. resolve project/user
  3. resolve capability/tool
  4. check whether tool is live
  5. check whether credentials are available
  6. check wallet balance
  7. atomically deduct cost
  8. execute capability
  9. write execution log
  10. optionally refund on failure
  11. return response

  That is the complete execution/billing middleware path.

  ———

  # Final architecture summary

  ## MCP side

  Used by UFC for:

  - capability discovery
  - integration requests
  - endpoint manifest retrieval
  - docs/instructions retrieval

  ## HTTP side

  Used by deployed apps for:

  - actual runtime execution
  - billable requests
  - production workflows
  - scheduled jobs
  - webhooks and automations

  ## Integrator side

  Used by FuseKit internally for:

  - reading docs
  - generating server runtime
  - publishing HTTP execution capabilities
  - producing manifests/docs
  - handling pending-credential states

  ———

  # One concrete example end-to-end

  User says:

  > “Build me an app that checks Product Hunt and sends me an SMS after 3 hours.”

  ### Build time

  1. UFC checks FuseKit MCP
  2. sees get_producthunt and send_sms already exist
  3. UFC retrieves their HTTP endpoint contracts
  4. UFC builds the app with:
      - scheduler
      - call FuseKit Product Hunt endpoint
      - then call FuseKit SMS endpoint

  ### Runtime

  5. after 3 hours, the deployed app calls FuseKit HTTP endpoint for Product Hunt
  6. FuseKit deducts wallet credits
  7. FuseKit returns Product Hunt result
  8. app then calls FuseKit HTTP endpoint for SMS send
  9. FuseKit deducts wallet credits
  10. SMS is sent

  If one capability were missing:

  - UFC would request integration through MCP first
  - FuseKit would generate and publish that capability
  - then UFC would wire it into the app

  ———

  # Final statement

  So the final pipeline is:

  - UFC uses MCP to discover and request capabilities
  - FuseKit backend generates and publishes server-side HTTP-backed capabilities
  - deployed apps call FuseKit HTTP endpoints at runtime
  - wallet deduction happens on every real HTTP execution request

  That is the correct end-to-end architecture for the proposition you want.

  If you want, I can next turn this into a hackathon-ready architecture diagram in plain text or a judge pitch explanation.