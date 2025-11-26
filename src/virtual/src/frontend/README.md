# Frontend Application

A React/TypeScript Single Page Application (SPA) for the Semantic Kernel Application, built with Semantic UI for a clean, responsive user interface.

## Overview

- **Framework**: React 17
- **Language**: TypeScript
- **UI Library**: Semantic UI React
- **Build Tool**: Webpack 5
- **Base Image**: Node 20 Alpine

## Project Structure

```
src/virtual/src/frontend/
├── .config/              # Build configuration
│   └── webpack.config.js # Webpack configuration
├── public/               # Static assets
├── src/                  # Source code
│   ├── components/       # React components
│   ├── pages/           # Page components
│   ├── services/        # API service clients
│   ├── hooks/           # Custom React hooks
│   ├── types/           # TypeScript definitions
│   └── main.ts          # Application entry point
├── package.json         # Dependencies and scripts
└── tsconfig.json        # TypeScript configuration
```

## Prerequisites

- Node.js 18+ (20 recommended)
- npm 9+

## Getting Started

### Installation

```bash
# Navigate to frontend directory
cd src/virtual/src/frontend

# Install dependencies
npm install
```

### Development Server

```bash
# Start development server with hot reload
npm run dev
```

The development server runs at `http://localhost:3000` with:

- Hot Module Replacement (HMR)
- Source maps for debugging
- TypeScript type checking

### Production Build

```bash
# Create optimized production build
npm run build
```

Output is placed in `dist/` directory.

## Available Scripts

| Script               | Description                              |
| -------------------- | ---------------------------------------- |
| `npm run dev`        | Start development server with hot reload |
| `npm run start`      | Start development server                 |
| `npm run build`      | Create production build                  |
| `npm test`           | Run unit tests                           |
| `npm run lint`       | Run ESLint                               |
| `npm run lint:fix`   | Fix ESLint issues                        |
| `npm run type-check` | TypeScript type checking                 |
| `npm run format`     | Format code with Prettier                |

## Configuration

### Environment Variables

Create a `.env` file for environment-specific configuration:

```env
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080
```

### TypeScript Configuration

The `tsconfig.json` includes strict type checking:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

### Webpack Configuration

Custom webpack configuration is in `.config/webpack.config.js`:

- TypeScript compilation via `ts-loader`
- CSS handling with `css-loader` and `style-loader`
- HTML template processing
- Development server configuration

## Dependencies

### Production

- `react` / `react-dom` - UI framework
- `axios` - HTTP client
- `semantic-ui-react` - UI component library
- `semantic-ui-css` - UI styling

### Development

- `typescript` - Type checking
- `webpack` / `webpack-cli` / `webpack-dev-server` - Build tools
- `eslint` - Code linting
- `prettier` - Code formatting
- `jest` / `ts-jest` - Testing framework

## Code Quality

### ESLint

ESLint is configured with TypeScript and React plugins:

```bash
# Check for issues
npm run lint

# Auto-fix issues
npm run lint:fix
```

### Prettier

Code formatting is enforced via Prettier:

```bash
npm run format
```

### Type Checking

Run TypeScript compiler in check mode:

```bash
npm run type-check
```

## Testing

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

## Docker Development

### Running with Docker Compose

```bash
# Start frontend service
docker-compose up frontend

# View logs
docker-compose logs -f frontend
```

### Development Container

The frontend is included in the devcontainer setup with:

- Hot reload via volume mounts
- Debug port exposed (9229)
- Node.js debugger support

## Integration Points

The frontend communicates with:

- **Gateway API**: All API requests route through the gateway
- **WebSocket**: Real-time updates for chat functionality

## Browser Support

Based on `browserslist` configuration:

- Last 2 versions of major browsers
- No IE11 support
- No Opera Mini support

```json
{
  "browserslist": [">0.2%", "not dead", "not op_mini all"]
}
```

## Resource Limits

| Resource | Production | Development |
| -------- | ---------- | ----------- |
| CPU      | 0.5        | 1.0         |
| Memory   | 256MB      | 512MB       |

## Port Mapping

| Port | Description                 |
| ---- | --------------------------- |
| 3000 | Frontend application        |
| 9229 | Node.js debugger (dev only) |

## Troubleshooting

### Common Issues

1. **Module Not Found**

   ```bash
   # Clear node_modules and reinstall
   rm -rf node_modules
   npm install
   ```

2. **TypeScript Errors**

   ```bash
   # Check for type errors
   npm run type-check
   ```

3. **Hot Reload Not Working**
   - Ensure webpack-dev-server is running
   - Check for file watch limits on Linux

4. **Build Failures**
   - Clear webpack cache
   - Check for circular dependencies

### Debug Mode

To debug in VS Code:

1. Start the dev server: `npm run dev`
2. Open VS Code Debug panel
3. Use "Attach to Chrome" configuration
4. Set breakpoints in TypeScript files

## Related Documentation

- [Architecture Overview](../../ARCHITECTURE.md)
- [Development Guide](../../DEVELOPMENT.md)
- [Backend API](../backend/README.md)
- [E2E Tests](../../tests/README.md)
