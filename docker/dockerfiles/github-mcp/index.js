#!/usr/bin/env node
/**
 * GitHub MCP Server
 * Model Context Protocol server for GitHub integration
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Octokit } from "@octokit/rest";
import dotenv from "dotenv";
import { z } from "zod";

// Load environment variables
dotenv.config();

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || "";
const octokit = GITHUB_TOKEN
  ? new Octokit({ auth: GITHUB_TOKEN })
  : new Octokit();

// Tool schemas using Zod
const GetRepoSchema = z.object({
  owner: z.string().describe("Repository owner (username or organization)"),
  repo: z.string().describe("Repository name"),
});

const SearchCodeSchema = z.object({
  query: z.string().describe("Search query for code"),
  owner: z.string().optional().describe("Limit to specific owner"),
  repo: z.string().optional().describe("Limit to specific repo"),
  per_page: z.number().default(30).describe("Results per page (max 100)"),
});

const GetFileContentsSchema = z.object({
  owner: z.string().describe("Repository owner"),
  repo: z.string().describe("Repository name"),
  path: z.string().describe("File path in repository"),
  ref: z.string().optional().describe("Git ref (branch, tag, or commit SHA)"),
});

const ListIssuesSchema = z.object({
  owner: z.string().describe("Repository owner"),
  repo: z.string().describe("Repository name"),
  state: z.enum(["open", "closed", "all"]).default("open"),
  per_page: z.number().default(30),
});

const CreateIssueSchema = z.object({
  owner: z.string().describe("Repository owner"),
  repo: z.string().describe("Repository name"),
  title: z.string().describe("Issue title"),
  body: z.string().optional().describe("Issue body"),
  labels: z.array(z.string()).optional().describe("Labels to apply"),
});

// Define available tools
const tools = [
  {
    name: "github_get_repo",
    description: "Get information about a GitHub repository",
    inputSchema: {
      type: "object",
      properties: {
        owner: { type: "string", description: "Repository owner" },
        repo: { type: "string", description: "Repository name" },
      },
      required: ["owner", "repo"],
    },
  },
  {
    name: "github_search_code",
    description: "Search for code across GitHub repositories",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" },
        owner: { type: "string", description: "Limit to specific owner" },
        repo: { type: "string", description: "Limit to specific repo" },
        per_page: { type: "number", description: "Results per page" },
      },
      required: ["query"],
    },
  },
  {
    name: "github_get_file_contents",
    description: "Get contents of a file from a GitHub repository",
    inputSchema: {
      type: "object",
      properties: {
        owner: { type: "string", description: "Repository owner" },
        repo: { type: "string", description: "Repository name" },
        path: { type: "string", description: "File path" },
        ref: { type: "string", description: "Git ref" },
      },
      required: ["owner", "repo", "path"],
    },
  },
  {
    name: "github_list_issues",
    description: "List issues in a GitHub repository",
    inputSchema: {
      type: "object",
      properties: {
        owner: { type: "string", description: "Repository owner" },
        repo: { type: "string", description: "Repository name" },
        state: { type: "string", enum: ["open", "closed", "all"] },
        per_page: { type: "number" },
      },
      required: ["owner", "repo"],
    },
  },
  {
    name: "github_create_issue",
    description: "Create a new issue in a GitHub repository",
    inputSchema: {
      type: "object",
      properties: {
        owner: { type: "string", description: "Repository owner" },
        repo: { type: "string", description: "Repository name" },
        title: { type: "string", description: "Issue title" },
        body: { type: "string", description: "Issue body" },
        labels: { type: "array", items: { type: "string" } },
      },
      required: ["owner", "repo", "title"],
    },
  },
];

// Tool handlers
async function handleGetRepo(args) {
  const { owner, repo } = GetRepoSchema.parse(args);
  const response = await octokit.repos.get({ owner, repo });
  return {
    name: response.data.full_name,
    description: response.data.description,
    stars: response.data.stargazers_count,
    forks: response.data.forks_count,
    language: response.data.language,
    topics: response.data.topics,
    default_branch: response.data.default_branch,
    html_url: response.data.html_url,
  };
}

async function handleSearchCode(args) {
  const { query, owner, repo, per_page } = SearchCodeSchema.parse(args);
  let q = query;
  if (owner && repo) {
    q += ` repo:${owner}/${repo}`;
  } else if (owner) {
    q += ` user:${owner}`;
  }

  const response = await octokit.search.code({ q, per_page });
  return {
    total_count: response.data.total_count,
    items: response.data.items.map((item) => ({
      name: item.name,
      path: item.path,
      repository: item.repository.full_name,
      html_url: item.html_url,
    })),
  };
}

async function handleGetFileContents(args) {
  const { owner, repo, path, ref } = GetFileContentsSchema.parse(args);
  const response = await octokit.repos.getContent({
    owner,
    repo,
    path,
    ref,
  });

  if (Array.isArray(response.data)) {
    return { type: "directory", items: response.data.map((f) => f.name) };
  }

  if (response.data.type === "file" && "content" in response.data) {
    const content = Buffer.from(response.data.content, "base64").toString(
      "utf-8"
    );
    return { type: "file", content, sha: response.data.sha };
  }

  return { type: response.data.type, data: response.data };
}

async function handleListIssues(args) {
  const { owner, repo, state, per_page } = ListIssuesSchema.parse(args);
  const response = await octokit.issues.listForRepo({
    owner,
    repo,
    state,
    per_page,
  });

  return response.data.map((issue) => ({
    number: issue.number,
    title: issue.title,
    state: issue.state,
    labels: issue.labels.map((l) => (typeof l === "string" ? l : l.name)),
    created_at: issue.created_at,
    html_url: issue.html_url,
  }));
}

async function handleCreateIssue(args) {
  const { owner, repo, title, body, labels } = CreateIssueSchema.parse(args);
  const response = await octokit.issues.create({
    owner,
    repo,
    title,
    body,
    labels,
  });

  return {
    number: response.data.number,
    title: response.data.title,
    html_url: response.data.html_url,
  };
}

// Create MCP server
const server = new Server(
  {
    name: "github-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Register tool list handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

// Register tool call handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;
    switch (name) {
      case "github_get_repo":
        result = await handleGetRepo(args);
        break;
      case "github_search_code":
        result = await handleSearchCode(args);
        break;
      case "github_get_file_contents":
        result = await handleGetFileContents(args);
        break;
      case "github_list_issues":
        result = await handleListIssues(args);
        break;
      case "github_create_issue":
        result = await handleCreateIssue(args);
        break;
      default:
        throw new Error(`Unknown tool: ${name}`);
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("GitHub MCP Server running on stdio");
}

main().catch(console.error);
