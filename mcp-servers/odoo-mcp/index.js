/**
 * Odoo MCP Server
 * 
 * Provides Odoo ERP integration via Model Context Protocol.
 * Supports accounting operations: invoices, customers, payments, products.
 * 
 * Usage:
 *   node index.js
 * 
 * Configuration via environment variables:
 *   ODOO_URL - Odoo instance URL (default: http://localhost:8069)
 *   ODOO_DB - Database name (default: ai_employee)
 *   ODOO_USERNAME - Username/email (default: admin)
 *   ODOO_PASSWORD - Password
 *   ODOO_API_KEY - API key (optional)
 */

const { Server } = require('@modelcontextprotocol/sdk');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Load environment variables
const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069';
const ODOO_DB = process.env.ODOO_DB || 'ai_employee';
const ODOO_USERNAME = process.env.ODOO_USERNAME || 'admin';
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || '';
const ODOO_API_KEY = process.env.ODOO_API_KEY || '';

// Python connector path
const PYTHON_CONNECTOR = path.join(__dirname, '..', '..', 'scripts', 'odoo_connector.py');

class OdooMCPServer {
  constructor() {
    this.server = null;
    this.tools = this.defineTools();
  }

  defineTools() {
    return [
      {
        name: 'odoo_test_connection',
        description: 'Test connection to Odoo ERP instance',
        inputSchema: {
          type: 'object',
          properties: {}
        }
      },
      {
        name: 'odoo_create_invoice',
        description: 'Create a new invoice in Odoo for a customer',
        inputSchema: {
          type: 'object',
          properties: {
            customer_name: {
              type: 'string',
              description: 'Customer name'
            },
            customer_email: {
              type: 'string',
              description: 'Customer email (optional)'
            },
            amount: {
              type: 'number',
              description: 'Invoice amount (without tax)'
            },
            description: {
              type: 'string',
              description: 'Invoice description'
            },
            product_name: {
              type: 'string',
              description: 'Product/service name'
            },
            due_date: {
              type: 'string',
              description: 'Due date (YYYY-MM-DD format, optional)'
            },
            dry_run: {
              type: 'boolean',
              description: 'If true, simulate without creating'
            }
          },
          required: ['customer_name', 'amount']
        }
      },
      {
        name: 'odoo_get_invoices',
        description: 'Retrieve invoices from Odoo with optional filters',
        inputSchema: {
          type: 'object',
          properties: {
            customer_name: {
              type: 'string',
              description: 'Filter by customer name'
            },
            state: {
              type: 'string',
              description: 'Filter by state: draft, posted, paid, cancelled',
              enum: ['draft', 'posted', 'paid', 'cancelled']
            },
            last_days: {
              type: 'number',
              description: 'Filter by date (last N days)'
            }
          }
        }
      },
      {
        name: 'odoo_sync_invoices',
        description: 'Sync invoices from Odoo to local vault',
        inputSchema: {
          type: 'object',
          properties: {
            last_days: {
              type: 'number',
              description: 'Number of days to sync (default: 30)'
            }
          }
        }
      },
      {
        name: 'odoo_register_payment',
        description: 'Register a payment for an invoice',
        inputSchema: {
          type: 'object',
          properties: {
            invoice_id: {
              type: 'number',
              description: 'Odoo invoice ID'
            },
            amount: {
              type: 'number',
              description: 'Payment amount (default: full amount)'
            },
            payment_date: {
              type: 'string',
              description: 'Payment date (YYYY-MM-DD format)'
            },
            dry_run: {
              type: 'boolean',
              description: 'If true, simulate without creating'
            }
          },
          required: ['invoice_id']
        }
      },
      {
        name: 'odoo_list_customers',
        description: 'List all customers from Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            limit: {
              type: 'number',
              description: 'Maximum customers to return (default: 50)'
            }
          }
        }
      },
      {
        name: 'odoo_get_customer',
        description: 'Get customer details by name or email',
        inputSchema: {
          type: 'object',
          properties: {
            identifier: {
              type: 'string',
              description: 'Customer name or email'
            }
          },
          required: ['identifier']
        }
      }
    ];
  }

  async executePythonCommand(args) {
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn('python', [PYTHON_CONNECTOR, ...args], {
        env: {
          ...process.env,
          ODOO_URL,
          ODOO_DB,
          ODOO_USERNAME,
          ODOO_PASSWORD,
          ODOO_API_KEY
        }
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
    console.error(`Handling tool call: ${name}`);

    try {
      switch (name) {
        case 'odoo_test_connection': {
          const output = await this.executePythonCommand(['--test-connection']);
          return {
            content: [
              {
                type: 'text',
                text: output
              }
            ]
          };
        }

        case 'odoo_create_invoice': {
          const cmdArgs = ['--create-invoice'];
          cmdArgs.push('--customer', args.customer_name);
          if (args.customer_email) cmdArgs.push('--email', args.customer_email);
          cmdArgs.push('--amount', args.amount.toString());
          if (args.description) cmdArgs.push('--description', args.description);
          if (args.product_name) cmdArgs.push('--product', args.product_name);
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

        case 'odoo_get_invoices': {
          const cmdArgs = ['--sync-invoices', '--last-days', (args.last_days || 30).toString()];
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

        case 'odoo_sync_invoices': {
          const cmdArgs = ['--sync-invoices', '--last-days', (args.last_days || 30).toString()];
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

        case 'odoo_register_payment': {
          // Note: This would need additional implementation in odoo_connector.py
          return {
            content: [
              {
                type: 'text',
                text: 'Payment registration not yet implemented in connector'
              }
            ]
          };
        }

        case 'odoo_list_customers': {
          const cmdArgs = ['--list-customers'];
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

        case 'odoo_get_customer': {
          const cmdArgs = ['--get-customer', args.identifier];
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
    console.error('Starting Odoo MCP Server...');
    console.error(`Odoo URL: ${ODOO_URL}`);
    console.error(`Database: ${ODOO_DB}`);
    console.error(`Username: ${ODOO_USERNAME}`);

    // Create MCP server
    this.server = new Server(
      {
        name: 'odoo-mcp',
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
        console.error('Transport closed');
      },
      onerror: (err) => {
        console.error('Transport error:', err);
      }
    };

    await this.server.connect(transport);
    console.error('Odoo MCP Server started successfully');
  }
}

// Start server
const server = new OdooMCPServer();
server.start().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
