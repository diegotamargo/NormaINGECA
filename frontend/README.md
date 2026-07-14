# NormaINGECA Frontend

A modern and responsive frontend application for NormaINGECA, built with React and Vite. This project leverages fast development cycles and optimized production builds to deliver an efficient user experience with real-time chat capabilities and markdown rendering.

## Description

This project represents the frontend of the NormaINGECA system. Using React and Vite, it provides:

- **Fast Development**: Instant hot module replacement (HMR) with Vite for rapid iteration
- **Production Optimization**: Optimized builds with code splitting and tree-shaking
- **Responsive Design**: A seamless experience across desktops, tablets, and mobile devices
- **Advanced Markdown Support**: Integrated markdown rendering with KaTeX for mathematical expressions
- **Real-time Chat**: Streaming chat interface for interactive conversations
- **Reusable Components**: A modular structure built with React, promoting maintainability and scalability
- **API Integration**: Smooth communication with the FastAPI backend to manage chat sessions and data

## Features

- **Responsive UI**: Designed to work seamlessly on all devices with Material Design tokens
- **Markdown Rendering**: Full markdown support with KaTeX for mathematical formulas
- **Dark Mode**: Built-in dark mode support using Tailwind CSS
- **Streaming Responses**: Real-time chat message streaming from backend
- **Organized Component Structure**: Clear separation of concerns with feature-based folder organization
- **Custom Hooks**: Reusable logic for chat management and text animations
- **Easy Development**: Local development server with proxy to FastAPI backend

## Technologies Used

- **React.js**: JavaScript library for building user interfaces
- **Vite**: Next-generation frontend build tool for fast development and optimized production builds
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **markdown-it**: Markdown parser and renderer with plugin support
- **markdown-it-texmath**: KaTeX rendering plugin for markdown
- **KaTeX**: Fast math typesetting for LaTeX expressions

## Requirements

### Basic Requirements

- [Node.js](https://nodejs.org/) v16 or higher
- npm, yarn, or pnpm for package management
- FastAPI backend running on `http://localhost:58734` (configurable via `.env`)

### Optional

- Any modern web browser (Chrome, Firefox, Safari, Edge)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd NormaINGECA/frontend
```

### 2. Install Dependencies

```bash
npm install
# or
yarn install
# or
pnpm install
```

### 3. Environment Configuration

Create a `.env` file in the project root (optional, for custom API target):

```env
VITE_API_TARGET=http://localhost:58734
```

If not specified, the default API target is `http://localhost:58734`.

### 4. Run the Development Server

```bash
npm run dev
# or
yarn dev
```

The application will start at `http://localhost:5173` by default. Vite will automatically proxy `/api` requests to the backend.

### 5. Build for Production

```bash
npm run build
# or
yarn build
```

The optimized build will be output to the `dist/` directory.

### 6. Preview Production Build

```bash
npm run preview
# or
yarn preview
```

## Project Structure

The project follows a feature-based component organization:

```
frontend/
├── public/                          # Static assets (images, fonts, etc.)
├── src/
│   ├── api/
│   │   └── client.js               # API client for backend communication
│   ├── components/
│   │   ├── chat/                   # Chat-related components
│   │   │   ├── ChatHeader.jsx
│   │   │   ├── ChatInput.jsx
│   │   │   ├── ChatStream.jsx
│   │   │   ├── ChatView.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   └── ThinkingIndicator.jsx
│   │   ├── layout/                 # Layout components
│   │   │   ├── MobileHeader.jsx
│   │   │   └── Sidebar.jsx
│   │   └── sources/                # Source display components
│   │       └── SourcePanel.jsx
│   ├── hooks/                      # Custom React hooks
│   │   ├── useChat.js              # Chat state management
│   │   └── useSmoothText.js        # Text animation utilities
│   ├── lib/
│   │   └── markdown.js             # Markdown rendering utilities
│   ├── App.jsx                     # Main application component
│   ├── main.jsx                    # Application entry point
│   └── index.css                   # Global styles with Tailwind
├── index.html                      # HTML entry point
├── vite.config.js                 # Vite configuration
├── tailwind.config.js             # Tailwind CSS configuration
├── postcss.config.js              # PostCSS configuration
├── package.json                   # Project dependencies and scripts
└── .env.example                   # Example environment variables
```

## Coding Standards

This project follows best practices for React and JavaScript development:

### Code Quality Guidelines

- **File Naming**: Use PascalCase for React components (e.g., `ChatHeader.jsx`), camelCase for utilities and hooks (e.g., `useChat.js`)
- **Component Organization**: Keep components focused and single-responsibility
- **Props**: Use prop destructuring for clarity
- **Hooks**: Extract reusable logic into custom hooks
- **CSS**: Use Tailwind CSS utility classes for styling; avoid inline styles when possible
- **Performance**: Use React.memo for pure components to prevent unnecessary re-renders

### Recommended Tools and Configuration

While this project currently does not have ESLint or Prettier configured, it is **strongly recommended** to add them for consistency and code quality:

- **ESLint**: For JavaScript linting - [ESLint Documentation](https://eslint.org/docs/)
- **Prettier**: For code formatting - [Prettier Documentation](https://prettier.io/docs/en/index.html)
- **React Best Practices**: Follow the official React guidelines - [React Documentation](https://react.dev/)

### Setup ESLint (Recommended)

```bash
npm install --save-dev eslint eslint-plugin-react eslint-plugin-react-hooks
npx eslint --init
```

### Setup Prettier (Recommended)

```bash
npm install --save-dev prettier
# Create .prettierrc file with your preferences
```

## Deployment

This project is built to work seamlessly with the FastAPI backend:

### Local Deployment

1. Ensure the FastAPI backend is running on the configured API target
2. Build the project: `npm run build`
3. The backend serves the `dist/` folder as static files at `/`

### Cloud Deployment

For deploying to cloud platforms (Vercel, Netlify, etc.):

1. Build the project: `npm run build`
2. Deploy the `dist/` folder to your hosting service
3. Configure the API target via environment variables to point to your deployed backend

## Contributions

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a new branch for your feature or fix (`git checkout -b feature/your-feature`)
3. Follow the coding standards mentioned above
4. Commit your changes with clear messages
5. Open a pull request describing your changes

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For questions or issues, please reach out to the development team.
