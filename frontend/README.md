# NOM Chat Agent Frontend

A modern Next.js chat interface for the NOM Chat Agent backend.

## Features

- 🎨 Clean, modern UI with warm color scheme (inspired by Anthropic's Claude design)
- 💬 Real-time chat interface
- 📝 Markdown rendering with syntax highlighting
- 🎯 Session-based conversations
- ⚡ Responsive design with Tailwind CSS
- 🔗 Easy backend integration

## Setup

### Prerequisites

- Node.js 18+
- pnpm (or npm/yarn)

### Installation

```bash
# Install dependencies
pnpm install
```

### Environment Setup

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8000
```

Update `NEXT_PUBLIC_BACKEND_BASE_URL` to match your backend server address.

### Development

```bash
# Start development server
pnpm dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
# Build for production
pnpm build

# Start production server
pnpm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main chat page
│   └── globals.css        # Global styles
├── components/
│   ├── chat/              # Chat-related components
│   │   ├── ChatInput.tsx  # Message input field
│   │   ├── Message.tsx    # Individual message display
│   │   └── MessageList.tsx # Message list container
│   ├── markdown/          # Markdown rendering
│   │   ├── CodeBlock.tsx  # Syntax-highlighted code blocks
│   │   └── MarkdownContent.tsx # Markdown renderer
│   └── ui/                # UI primitives (shadcn)
│       └── button.tsx     # Button component
├── lib/
│   ├── api.ts            # Backend API client
│   └── types.ts          # TypeScript type definitions
└── package.json

```

## Backend Integration

The frontend expects the following backend API endpoints:

### Create Session

```
POST /session
Response: { sessionId: string }
```

### Send Message

```
POST /chat
Body: { sessionId: string, message: string }
Response: { sessionId: string, messages: Message[], status: "success" | "error", error?: string }
```

### Get History

```
GET /history/:sessionId
Response: { messages: Message[] }
```

Where `Message` should have:

```typescript
{
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}
```

## Styling

The UI uses:

- **Tailwind CSS** for utility-based styling
- **shadcn/ui** for component primitives
- **Lucide React** for icons
- **Design scheme**: Warm coral (#cc785c) primary color with cream/slate palette

## Key Technologies

- **Framework**: Next.js 16
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4
- **Components**: shadcn/ui, @base-ui/react
- **Markdown**: react-markdown
- **Code Highlighting**: highlight.js
- **Icons**: lucide-react

## Development Notes

- The chat maintains session state across reloads via session ID
- Messages are rendered with markdown support, including code blocks
- The UI is fully responsive and works on mobile devices
- No authentication is required at this point

## Troubleshooting

### Backend connection failed

- Ensure the backend is running on the URL specified in `.env.local`
- Check CORS headers if making cross-origin requests
- Verify the backend is exposing the required endpoints

### Markdown not rendering

- Check that react-markdown is properly installed
- Verify the message content is valid markdown

### Styles not applying

- Run `pnpm install` to ensure Tailwind CSS is properly configured
- Check that `globals.css` is imported in layout.tsx

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
