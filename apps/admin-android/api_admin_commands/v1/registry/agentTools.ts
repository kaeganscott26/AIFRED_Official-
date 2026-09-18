/**
 * AIFRED Android Admin — Agent Tooling
 *
 * Turns the Admin LLM from a chat-only model into a project-aware agent.
 *
 * Scope:
 *   - AIFRED Android Admin project
 *   - Files available to the agent workspace
 *   - Git inspection / changes
 *   - Shell commands
 *   - Web search / fetch
 *   - Existing AIFRED Admin API
 *
 * This module intentionally does NOT expose:
 *   - website deployment/admin
 *   - Cloudflare production operations
 *   - desktop admin
 *   - arbitrary remote infrastructure
 *
 * The LLM is the reasoning layer.
 * This registry is the capability layer.
 */

export type ToolContext = {
  workspaceRoot: string;
  conversationId?: string;
  sessionId?: string;
};

export type ToolDefinition = {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  requiresApproval?: boolean;
};

export type ToolCall = {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
};

export type ToolResult = {
  ok: boolean;
  tool: string;
  output?: unknown;
  error?: string;
};

/**
 * Optional host implementation.
 *
 * The Android/Admin runtime supplies these functions.
 * This keeps the agent layer independent of the actual filesystem,
 * Git implementation, HTTP implementation, or LLM provider.
 */
export type AgentHost = {
  readFile: (path: string) => Promise<string>;

  writeFile: (
    path: string,
    contents: string
  ) => Promise<void>;

  listFiles: (
    path: string
  ) => Promise<unknown>;

  searchFiles: (
    query: string,
    path?: string
  ) => Promise<unknown>;

  deleteFile?: (
    path: string
  ) => Promise<void>;

  runCommand: (
    command: string,
    cwd: string
  ) => Promise<{
    stdout: string;
    stderr: string;
    exitCode: number;
  }>;

  webSearch?: (
    query: string
  ) => Promise<unknown>;

  webFetch?: (
    url: string
  ) => Promise<unknown>;

  adminRequest?: (
    path: string,
    options?: {
      method?: string;
      body?: unknown;
    }
  ) => Promise<unknown>;
};


/* -------------------------------------------------------------------------- */
/* Safety                                                                      */
/* -------------------------------------------------------------------------- */

function resolveWorkspacePath(
  root: string,
  requested: string
): string {
  const normalizedRoot = root.replace(/\\/g, "/").replace(/\/+$/, "");
  const normalizedPath = requested
    .replace(/\\/g, "/")
    .replace(/^\/+/, "");

  const full = `${normalizedRoot}/${normalizedPath}`
    .replace(/\/+/g, "/");

  if (
    full !== normalizedRoot &&
    !full.startsWith(`${normalizedRoot}/`)
  ) {
    throw new Error(
      `Path escapes the Android Admin workspace: ${requested}`
    );
  }

  if (
    normalizedPath.includes("../") ||
    normalizedPath === ".."
  ) {
    throw new Error(
      `Parent-directory traversal is not allowed: ${requested}`
    );
  }

  return full;
}


/* -------------------------------------------------------------------------- */
/* Tool registry                                                               */
/* -------------------------------------------------------------------------- */

export class AndroidAdminToolRegistry {
  private readonly tools = new Map<
    string,
    ToolDefinition
  >();

  private readonly handlers = new Map<
    string,
    (
      args: Record<string, unknown>,
      ctx: ToolContext
    ) => Promise<unknown>
  >();

  constructor(
    private readonly host: AgentHost
  ) {
    this.registerBuiltInTools();
  }

  register(
    definition: ToolDefinition,
    handler: (
      args: Record<string, unknown>,
      ctx: ToolContext
    ) => Promise<unknown>
  ) {
    this.tools.set(definition.name, definition);
    this.handlers.set(definition.name, handler);
  }

  definitions(): ToolDefinition[] {
    return [...this.tools.values()];
  }

  async execute(
    call: ToolCall,
    ctx: ToolContext
  ): Promise<ToolResult> {
    const definition = this.tools.get(call.name);
    const handler = this.handlers.get(call.name);

    if (!definition || !handler) {
      return {
        ok: false,
        tool: call.name,
        error: `Unknown tool: ${call.name}`,
      };
    }

    try {
      const output = await handler(call.arguments, ctx);

      return {
        ok: true,
        tool: call.name,
        output,
      };
    } catch (error) {
      return {
        ok: false,
        tool: call.name,
        error:
          error instanceof Error
            ? error.message
            : String(error),
      };
    }
  }

  private registerBuiltInTools() {
    this.registerFileTools();
    this.registerGitTools();
    this.registerShellTool();
    this.registerWebTools();
    this.registerAdminTools();
  }


  /* ------------------------------------------------------------------------ */
  /* Files                                                                     */
  /* ------------------------------------------------------------------------ */

  private registerFileTools() {
    this.register(
      {
        name: "project.list",
        description:
          "List files and directories in the Android Admin project.",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description:
                "Workspace-relative directory path.",
            },
          },
        },
      },
      async (args, ctx) => {
        const path = String(args.path ?? ".");
        const safePath =
          path === "."
            ? ctx.workspaceRoot
            : resolveWorkspacePath(
                ctx.workspaceRoot,
                path
              );

        return this.host.listFiles(safePath);
      }
    );

    this.register(
      {
        name: "project.read",
        description:
          "Read a source file from the Android Admin project.",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description:
                "Workspace-relative file path.",
            },
          },
          required: ["path"],
        },
      },
      async (args, ctx) => {
        const path = resolveWorkspacePath(
          ctx.workspaceRoot,
          String(args.path)
        );

        return this.host.readFile(path);
      }
    );

    this.register(
      {
        name: "project.search",
        description:
          "Search the Android Admin project for code, symbols, strings, API routes, configuration, or references.",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
            },
            path: {
              type: "string",
            },
          },
          required: ["query"],
        },
      },
      async (args, ctx) => {
        return this.host.searchFiles(
          String(args.query),
          args.path
            ? resolveWorkspacePath(
                ctx.workspaceRoot,
                String(args.path)
              )
            : ctx.workspaceRoot
        );
      }
    );

    this.register(
      {
        name: "project.write",
        description:
          "Create or replace a file in the Android Admin project.",
        requiresApproval: true,
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
            },
            contents: {
              type: "string",
            },
          },
          required: ["path", "contents"],
        },
      },
      async (args, ctx) => {
        const path = resolveWorkspacePath(
          ctx.workspaceRoot,
          String(args.path)
        );

        await this.host.writeFile(
          path,
          String(args.contents)
        );

        return {
          written: true,
          path,
        };
      }
    );

    this.register(
      {
        name: "project.delete",
        description:
          "Delete a file from the Android Admin project.",
        requiresApproval: true,
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
            },
          },
          required: ["path"],
        },
      },
      async (args, ctx) => {
        if (!this.host.deleteFile) {
          throw new Error(
            "File deletion is not available in this host."
          );
        }

        const path = resolveWorkspacePath(
          ctx.workspaceRoot,
          String(args.path)
        );

        await this.host.deleteFile(path);

        return {
          deleted: true,
          path,
        };
      }
    );
  }


  /* ------------------------------------------------------------------------ */
  /* Git                                                                       */
  /* ------------------------------------------------------------------------ */

  private registerGitTools() {
    const git = (
      name: string,
      description: string,
      command: string,
      requiresApproval = false
    ) => {
      this.register(
        {
          name,
          description,
          requiresApproval,
          inputSchema: {
            type: "object",
            properties: {},
          },
        },
        async (_args, ctx) => {
          const result =
            await this.host.runCommand(
              command,
              ctx.workspaceRoot
            );

          return {
            command,
            ...result,
          };
        }
      );
    };

    git(
      "git.status",
      "Inspect the current Git working tree.",
      "git status --short --branch"
    );

    git(
      "git.diff",
      "Inspect current uncommitted changes.",
      "git diff --stat && git diff"
    );

    git(
      "git.log",
      "Inspect recent Git history.",
      "git log --oneline -20"
    );

    git(
      "git.branches",
      "List local and remote Git branches.",
      "git branch -a"
    );

    git(
      "git.pull",
      "Pull the latest changes for the current branch.",
      "git pull",
      true
    );

    git(
      "git.commit",
      "Commit staged changes.",
      "git commit",
      true
    );

    git(
      "git.push",
      "Push the current branch to its configured remote.",
      "git push",
      true
    );
  }


  /* ------------------------------------------------------------------------ */
  /* Shell                                                                     */
  /* ------------------------------------------------------------------------ */

  private registerShellTool() {
    this.register(
      {
        name: "project.run",
        description:
          "Run a development/test/build command inside the Android Admin project.",
        requiresApproval: true,
        inputSchema: {
          type: "object",
          properties: {
            command: {
              type: "string",
              description:
                "Command to execute.",
            },
          },
          required: ["command"],
        },
      },
      async (args, ctx) => {
        const command = String(args.command);

        /*
         * Keep execution inside the Android Admin workspace.
         * The host may add stronger platform-specific restrictions.
         */
        return this.host.runCommand(
          command,
          ctx.workspaceRoot
        );
      }
    );
  }


  /* ------------------------------------------------------------------------ */
  /* Web                                                                       */
  /* ------------------------------------------------------------------------ */

  private registerWebTools() {
    if (this.host.webSearch) {
      this.register(
        {
          name: "web.search",
          description:
            "Search the web for documentation, APIs, Android information, libraries, GitHub references, or technical research.",
          inputSchema: {
            type: "object",
            properties: {
              query: {
                type: "string",
              },
            },
            required: ["query"],
          },
        },
        async (args) => {
          return this.host.webSearch!(
            String(args.query)
          );
        }
      );
    }

    if (this.host.webFetch) {
      this.register(
        {
          name: "web.fetch",
          description:
            "Fetch a webpage or technical documentation page for the agent to inspect.",
          inputSchema: {
            type: "object",
            properties: {
              url: {
                type: "string",
                description:
                  "HTTPS URL to fetch.",
              },
            },
            required: ["url"],
          },
        },
        async (args) => {
          const url = String(args.url);

          if (!/^https:\/\//i.test(url)) {
            throw new Error(
              "web.fetch only accepts HTTPS URLs."
            );
          }

          return this.host.webFetch!(url);
        }
      );
    }
  }


  /* ------------------------------------------------------------------------ */
  /* AIFRED Admin                                                             */
  /* ------------------------------------------------------------------------ */

  private registerAdminTools() {
    if (!this.host.adminRequest) {
      return;
    }

    this.register(
      {
        name: "aifred.admin.inspect",
        description:
          "Inspect information exposed to the authenticated AIFRED Android Admin session. Use this for status audits and operational diagnostics.",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description:
                "An existing Android Admin API route.",
            },
          },
          required: ["path"],
        },
      },
      async (args) => {
        const path = String(args.path);

        /*
         * Deliberately prevent the generic agent from reaching
         * website/ops/desktop surfaces.
         */
        if (
          path.includes("/ops") ||
          path.includes("cloudflare") ||
          path.includes("deploy") ||
          path.includes("desktop")
        ) {
          throw new Error(
            "This agent is restricted to Android Admin operations."
          );
        }

        return this.host.adminRequest!(
          path,
          {
            method: "GET",
          }
        );
      }
    );
  }
}


/* -------------------------------------------------------------------------- */
/* LLM adapter helpers                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Converts our internal definitions into OpenAI-compatible
 * function/tool definitions.
 *
 * This means your existing chat-completions implementation can
 * receive the tools without changing the actual tool implementations.
 */
export function toLLMTools(
  registry: AndroidAdminToolRegistry
) {
  return registry.definitions().map(tool => ({
    type: "function",
    function: {
      name: tool.name,
      description: tool.description,
      parameters: tool.inputSchema,
    },
  }));
}


/**
 * Extract tool calls from an OpenAI-compatible assistant response.
 *
 * Your existing LLM provider can feed the returned calls into
 * registry.execute().
 */
export function extractToolCalls(
  message: any
): ToolCall[] {
  const calls = message?.tool_calls;

  if (!Array.isArray(calls)) {
    return [];
  }

  return calls.map((call: any) => {
    let args: Record<string, unknown> = {};

    try {
      args =
        typeof call.function?.arguments === "string"
          ? JSON.parse(
              call.function.arguments
            )
          : call.function?.arguments ?? {};
    } catch {
      throw new Error(
        `Invalid JSON arguments from tool ${call.function?.name}`
      );
    }

    return {
      id:
        call.id ??
        crypto.randomUUID(),
      name: call.function?.name,
      arguments: args,
    };
  });
}


/* -------------------------------------------------------------------------- */
/* Agent execution                                                            */
/* -------------------------------------------------------------------------- */

export type AgentModel = {
  complete: (request: {
    messages: any[];
    tools: ReturnType<typeof toLLMTools>;
  }) => Promise<{
    message: any;
    finishReason?: string;
  }>;
};


export type AgentRunOptions = {
  maxSteps?: number;

  /**
   * Called before a tool marked requiresApproval executes.
   *
   * Return true to allow.
   * Return false to reject.
   */
  approveTool?: (
    call: ToolCall
  ) => Promise<boolean>;
};


/**
 * Actual agent loop.
 *
 * This is the piece your current chatbot is missing.
 */
export async function runAndroidAdminAgent(
  model: AgentModel,
  registry: AndroidAdminToolRegistry,
  context: ToolContext,
  userMessage: string,
  options: AgentRunOptions = {}
) {
  const maxSteps =
    options.maxSteps ?? 20;

  const messages: any[] = [
    {
      role: "system",
      content: `
You are the AIFRED Android Admin engineering agent.

You are operating ONLY on the Android Admin side of AIFRED.

Your job is to inspect, understand, diagnose, research, and when
authorized modify the Android Admin project.

You are project-aware.

Before making claims about the project:
- inspect the relevant files;
- inspect Git state when useful;
- search the codebase instead of guessing;
- use web tools for current documentation when appropriate;
- distinguish observed facts from hypotheses.

When fixing something:
1. inspect;
2. identify the relevant code;
3. make the smallest appropriate change;
4. run relevant tests/build/checks;
5. inspect the result;
6. report what changed and what was verified.

Never claim that a command succeeded unless you actually
received a successful result.

You do NOT have authority over:
- AIFRED website operations;
- Cloudflare production operations;
- desktop admin;
- unrelated repositories;
- arbitrary infrastructure.

Do not attempt to access those surfaces.

For status audits, gather evidence first and produce:
- observed state;
- relevant files;
- problems found;
- evidence;
- likely cause;
- recommended next action.

Do not modify files during an audit unless explicitly asked.
      `.trim(),
    },

    {
      role: "user",
      content: userMessage,
    },
  ];

  const trace: Array<{
    step: number;
    tool?: string;
    result?: unknown;
  }> = [];

  for (
    let step = 0;
    step < maxSteps;
    step++
  ) {
    const completion =
      await model.complete({
        messages,
        tools: toLLMTools(registry),
      });

    const message =
      completion.message;

    messages.push(message);

    const calls =
      extractToolCalls(message);

    if (calls.length === 0) {
      return {
        ok: true,
        finalMessage:
          message?.content ?? "",
        messages,
        trace,
      };
    }

    for (const call of calls) {
      const definition =
        registry
          .definitions()
          .find(
            tool =>
              tool.name === call.name
          );

      if (!definition) {
        messages.push({
          role: "tool",
          tool_call_id: call.id,
          content: JSON.stringify({
            ok: false,
            error:
              `Tool ${call.name} is not registered.`,
          }),
        });

        continue;
      }

      if (
        definition.requiresApproval &&
        options.approveTool
      ) {
        const approved =
          await options.approveTool(
            call
          );

        if (!approved) {
          const rejected = {
            ok: false,
            tool: call.name,
            
