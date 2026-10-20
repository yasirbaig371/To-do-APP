import { apiRequest } from "./client";
import type { ChatMessage, ChatResponse } from "../types";

export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  confirm = false,
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, history, confirm }),
  });
}
