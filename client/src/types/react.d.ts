declare module 'react' {
  export = React;
  export as namespace React;
}

declare module 'react/jsx-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module 'react-router-dom' {
  export const BrowserRouter: any;
  export const Link: any;
  export const Route: any;
  export const Routes: any;
  export const Navigate: any;
  export const useNavigate: any;
}

declare module '@mantine/core' {
  export const MantineProvider: any;
  export const Text: any;
  export const Button: any;
  export const Group: any;
  export const Card: any;
  export const Paper: any;
  export const Title: any;
  export const Alert: any;
  export const TextInput: any;
  export const PasswordInput: any;
  export const Select: any;
  export const Badge: any;
  export const Grid: any;
  export const AppShell: any;
  export const Loader: any;
  export const Center: any;
} 