/**
 * Calendar MCP Server
 *
 * Provides calendar event management via Model Context Protocol.
 * Supports creating, reading, updating, deleting, and searching events.
 * Uses local ICS file storage - no external API required.
 *
 * Usage:
 *   node index.js
 *
 * Configuration via environment variables:
 *   VAULT_PATH - Path to Obsidian vault (default: AI_Employee_Vault)
 */

const { Server } = require('@modelcontextprotocol/sdk');
const { spawn } = require('child_process');
const path = require('path');

// Load environment variables
const VAULT_PATH = process.env.VAULT_PATH || 'AI_Employee_Vault';

// Python tool path
const PYTHON_TOOL = path.join(__dirname, '..', '..', 'scripts', 'calendar_tool.py');

class CalendarMCPServer {
  constructor() {
    this.server = null;
    this.tools = this.defineTools();
  }

  defineTools() {
    return [
      {
        name: 'calendar_create_event',
        description: 'Create a new calendar event in the AI Employee vault',
        inputSchema: {
          type: 'object',
          properties: {
            title: {
              type: 'string',
              description: 'Event title'
            },
            start: {
              type: 'string',
              description: 'Start datetime (YYYY-MM-DDTHH:MM:SS format)'
            },
            end: {
              type: 'string',
              description: 'End datetime (YYYY-MM-DDTHH:MM:SS format)'
            },
            description: {
              type: 'string',
              description: 'Event description (optional)'
            },
            location: {
              type: 'string',
              description: 'Event location (optional)'
            },
            categories: {
              type: 'array',
              items: { type: 'string' },
              description: 'Categories/tags for the event (optional)'
            },
            status: {
              type: 'string',
              description: 'Event status: CONFIRMED, TENTATIVE, or CANCELLED',
              enum: ['CONFIRMED', 'TENTATIVE', 'CANCELLED'],
              default: 'CONFIRMED'
            },
            priority: {
              type: 'number',
              description: 'Priority level (1-9, 1=highest, default: 5)',
              default: 5
            },
            reminder_minutes: {
              type: 'number',
              description: 'Minutes before event to send reminder (default: 15)',
              default: 15
            },
            dry_run: {
              type: 'boolean',
              description: 'If true, simulate without creating event'
            }
          },
          required: ['title', 'start', 'end']
        }
      },
      {
        name: 'calendar_list_events',
        description: 'List upcoming calendar events',
        inputSchema: {
          type: 'object',
          properties: {
            days: {
              type: 'number',
              description: 'Number of days ahead to look (default: 7)',
              default: 7
            },
            categories: {
              type: 'array',
              items: { type: 'string' },
              description: 'Filter by categories (optional)'
            },
            status: {
              type: 'string',
              description: 'Filter by status (optional)',
              enum: ['CONFIRMED', 'TENTATIVE', 'CANCELLED']
            },
            include_past: {
              type: 'boolean',
              description: 'Include past events in results',
              default: false
            }
          }
        }
      },
      {
        name: 'calendar_get_event',
        description: 'Get details for a specific calendar event by ID',
        inputSchema: {
          type: 'object',
          properties: {
            event_id: {
              type: 'string',
              description: 'Unique event ID (e.g., event-20260415-100000-abc123)'
            }
          },
          required: ['event_id']
        }
      },
      {
        name: 'calendar_update_event',
        description: 'Update an existing calendar event',
        inputSchema: {
          type: 'object',
          properties: {
            event_id: {
              type: 'string',
              description: 'Event ID to update'
            },
            title: {
              type: 'string',
              description: 'New title (optional)'
            },
            start: {
              type: 'string',
              description: 'New start time (optional)'
            },
            end: {
              type: 'string',
              description: 'New end time (optional)'
            },
            description: {
              type: 'string',
              description: 'New description (optional)'
            },
            location: {
              type: 'string',
              description: 'New location (optional)'
            },
            categories: {
              type: 'array',
              items: { type: 'string' },
              description: 'New categories (optional)'
            },
            status: {
              type: 'string',
              description: 'New status (optional)',
              enum: ['CONFIRMED', 'TENTATIVE', 'CANCELLED']
            },
            priority: {
              type: 'number',
              description: 'New priority (optional)'
            }
          },
          required: ['event_id']
        }
      },
      {
        name: 'calendar_delete_event',
        description: 'Delete a calendar event',
        inputSchema: {
          type: 'object',
          properties: {
            event_id: {
              type: 'string',
              description: 'Event ID to delete'
            }
          },
          required: ['event_id']
        }
      },
      {
        name: 'calendar_search_events',
        description: 'Search calendar events by title, description, or categories',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query string'
            }
          },
          required: ['query']
        }
      },
      {
        name: 'calendar_check_conflicts',
        description: 'Check for scheduling conflicts in a time range',
        inputSchema: {
          type: 'object',
          properties: {
            start: {
              type: 'string',
              description: 'Start of time range (YYYY-MM-DDTHH:MM:SS)'
            },
            end: {
              type: 'string',
              description: 'End of time range (YYYY-MM-DDTHH:MM:SS)'
            },
            exclude_id: {
              type: 'string',
              description: 'Event ID to exclude from conflict check (optional)'
            }
          },
          required: ['start', 'end']
        }
      },
      {
        name: 'calendar_get_day_schedule',
        description: 'Get all events scheduled for a specific day',
        inputSchema: {
          type: 'object',
          properties: {
            date: {
              type: 'string',
              description: 'Date to get schedule for (YYYY-MM-DD format)'
            }
          },
          required: ['date']
        }
      }
    ];
  }

  async executePythonCommand(args) {
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python', [PYTHON_TOOL, ...args], {
        env: {
          ...process.env,
          VAULT_PATH
        },
        shell: true  // Use shell for better Windows compatibility
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve(stdout);
        } else {
          reject(new Error(`Python process exited with code ${code}: ${stderr}`));
        }
      });

      pythonProcess.on('error', (err) => {
        reject(err);
      });
    });
  }

  async handleToolCall(name, args) {
    console.error(`Calendar MCP: Handling tool call: ${name}`);

    try {
      switch (name) {
        case 'calendar_create_event': {
          const cmdArgs = [
            '--vault', VAULT_PATH,
            '--json',
            'create',
            '--title', args.title,
            '--start', args.start,
            '--end', args.end
          ];

          if (args.description) cmdArgs.push('--description', args.description);
          if (args.location) cmdArgs.push('--location', args.location);
          if (args.categories && args.categories.length > 0) {
            cmdArgs.push('--categories', ...args.categories);
          }
          if (args.status) cmdArgs.push('--status', args.status);
          if (args.priority !== undefined) cmdArgs.push('--priority', args.priority.toString());
          if (args.reminder_minutes !== undefined) cmdArgs.push('--reminder', args.reminder_minutes.toString());
          if (args.dry_run) cmdArgs.push('--dry-run');

          const output = await this.executePythonCommand(cmdArgs);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        case 'calendar_list_events': {
          const cmdArgs = [
            '--vault', VAULT_PATH,
            '--json',
            'list',
            '--days', (args.days || 7).toString()
          ];

          if (args.categories && args.categories.length > 0) {
            cmdArgs.push('--categories', ...args.categories);
          }
          if (args.status) cmdArgs.push('--status', args.status);
          if (args.include_past) cmdArgs.push('--include-past');

          const output = await this.executePythonCommand(cmdArgs);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        case 'calendar_get_event': {
          const cmdArgs = [
            '--vault', VAULT_PATH,
            '--json',
            'get',
            '--event-id', args.event_id
          ];

          const output = await this.executePythonCommand(cmdArgs);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        case 'calendar_update_event': {
          const cmdArgs = [
            '--vault', VAULT_PATH,
            '--json',
            'update',
            '--event-id', args.event_id
          ];

          if (args.title) cmdArgs.push('--title', args.title);
          if (args.start) cmdArgs.push('--start', args.start);
          if (args.end) cmdArgs.push('--end', args.end);
          if (args.description) cmdArgs.push('--description', args.description);
          if (args.location) cmdArgs.push('--location', args.location);
          if (args.categories && args.categories.length > 0) {
            cmdArgs.push('--categories', ...args.categories);
          }
          if (args.status) cmdArgs.push('--status', args.status);
          if (args.priority !== undefined) cmdArgs.push('--priority', args.priority.toString());

          const output = await this.executePythonCommand(cmdArgs);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        case 'calendar_delete_event': {
          const cmdArgs = [
            '--vault', VAULT_PATH,
            '--json',
            'delete',
            '--event-id', args.event_id
          ];

          const output = await this.executePythonCommand(cmdArgs);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        case 'calendar_search_events': {
          const cmdArgs = [
            '--vault', VAULT_PATH,
            '--json',
            'search',
            '--query', args.query
          ];

          const output = await this.executePythonCommand(cmdArgs);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        case 'calendar_check_conflicts': {
          const cmdArgs = [
            '--vault', VAULT_PATH,
            '--json',
            'conflicts',
            '--start', args.start,
            '--end', args.end
          ];

          if (args.exclude_id) cmdArgs.push('--exclude-id', args.exclude_id);

          const output = await this.executePythonCommand(cmdArgs);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        case 'calendar_get_day_schedule': {
          const cmdArgs = [
            '--vault', VAULT_PATH,
            '--json',
            'day',
            '--date', args.date
          ];

          const output = await this.executePythonCommand(cmdArgs);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      console.error(`Error executing ${name}:`, error.message);
      return {
        content: [
          {
            type: 'text',
            text: `Error: ${error.message}`
          }
        ],
        isError: true
      };
    }
  }

  async start() {
    console.error('Starting Calendar MCP Server...');
    console.error(`Vault Path: ${VAULT_PATH}`);

    // Create MCP server
    this.server = new Server(
      {
        name: 'calendar-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Set up request handlers
    this.server.setRequestHandler('tools/list', async () => {
      return {
        tools: this.tools.map(tool => ({
          name: tool.name,
          description: tool.description,
          inputSchema: tool.inputSchema
        }))
      };
    });

    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      return await this.handleToolCall(name, args || {});
    });

    // Start the server
    const transport = {
      send: (message) => {
        process.stdout.write(JSON.stringify(message) + '\n');
      },
      onclose: () => {
        console.error('Calendar MCP transport closed');
      },
      onerror: (err) => {
        console.error('Calendar MCP transport error:', err);
      }
    };

    await this.server.connect(transport);
    console.error('Calendar MCP Server started successfully');
  }
}

// Start server
const server = new CalendarMCPServer();
server.start().catch((err) => {
  console.error('Failed to start Calendar MCP Server:', err);
  process.exit(1);
});
