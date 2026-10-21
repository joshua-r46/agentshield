# AgentShield

Runtime Security Infrastructure for Autonomous AI Agents.

AgentShield evaluates autonomous agent actions before they reach tools or APIs.

## Core Security Questions

1. What does the agent want to do?
2. Is the action safe and authorized?
3. Did the agent actually do what it claimed?

## Architecture

User
↓
Next.js Dashboard
↓
FastAPI Backend
↓
AgentShield Runtime
↓
Policy + Risk + Consequence Analysis
↓
Decision
↓
Tool/API

## Status

🚧 Hackathon MVP — In Development