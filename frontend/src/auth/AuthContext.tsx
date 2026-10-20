import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import * as authApi from "../api/auth";
import { setAccessToken } from "../api/client";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  ready: boolean;
  signIn(email: string, password: string): Promise<User>;
  signUp(fullName: string, email: string, password: string): Promise<void>;
  signOut(): Promise<void>;
  updateUser(user: User): void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await authApi.login(email, password);
    setAccessToken(result.access_token);
    setUser(result.user);
    return result.user;
  }, []);

  const signUp = useCallback(async (
    fullName: string,
    email: string,
    password: string,
  ) => {
    await authApi.register(fullName, email, password);
  }, []);

  const signOut = useCallback(async () => {
    try {
      if (user) await authApi.logoutRequest();
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, [user]);

  useEffect(() => {
    const handleUnauthorized = () => {
      setAccessToken(null);
      setUser(null);
    };
    window.addEventListener("todo:unauthorized", handleUnauthorized);
    return () =>
      window.removeEventListener("todo:unauthorized", handleUnauthorized);
  }, []);

  const value = useMemo(
    () => ({
      user,
      ready: true,
      signIn,
      signUp,
      signOut,
      updateUser: setUser,
    }),
    [user, signIn, signUp, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
