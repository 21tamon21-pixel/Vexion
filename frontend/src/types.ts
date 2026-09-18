export type PersonaTone =
  | "balanced"
  | "direct"
  | "friendly"
  | "professional";

export type PersonaVerbosity =
  | "concise"
  | "balanced"
  | "detailed";

export interface Persona {
  tone: PersonaTone;
  verbosity: PersonaVerbosity;
  system_prompt: string;
  voice_enabled?: boolean;
  auto_speak?: boolean;
  voice_name?: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  persona: Persona;
  created_at?: string;
}

export type Operation =
  | "chat"
  | "coding"
  | "build";

export interface ModelCosts {
  chat: number;
  coding: number;
  build: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  vendor: string;
  model: string;
  costs: ModelCosts;
  capabilities: Operation[];
  available: boolean;
  tagline: string;
  tier: number;
  requires_auth: boolean;
  provider_label: string;
  icon: string;
  premium: boolean;
  own_key: boolean;
  unavailable_reason: string;
}

export interface AppConfig {
  app_name: string;
  app_tagline: string;
  provider: string;
  model: string;
  provider_ready: boolean;
  features: {
    voice_input: boolean;
    voice_output: boolean;
    vision: boolean;
    web_search: boolean;
    image_generation: boolean;
    guest_mode: boolean;
  };
  models: ModelInfo[];
  free_model_id: string;
  weekly_credit_allowance: number;
  beta: {
    status: string;
    release_date: string;
    message: string;
  };
}

export interface CreditState {
  allowance: number;
  used: number;
  remaining: number;
  reset_at?: string | null;
  week_key?: string;
  cost?: number;
}

export interface UsageSummary {
  total_messages: number;
  total_conversations: number;
  total_projects: number;
  total_images: number;
  total_tokens: number;
  images_generated: number;
  quotas: any;
  storage: any;
  cache: any;

  credits_used: number;
  credits_remaining: number;
  weekly_credit_allowance: number;
  credits_reset_at?: string | null;

  by_model: { model_id: string; model_name: string; messages: number; approx_tokens: number }[];
  by_day: { day: string; messages: number }[];
  storage_bytes: number;
}

export interface Attachment {
  id: string;
  filename: string;
  kind: "image" | "document" | "text" | string;
  mime_type?: string;
  size_bytes?: number;
  url?: string;
  data_url?: string;
  pages?: number;
  size: number;
  extracted_text?: string;
}

export interface AttachmentRef {
  id: string;
  kind: string;
  filename: string;
}

export type MessageRole =
  | "user"
  | "assistant"
  | "system";

export type MessageStatus =
  | "streaming"
  | "complete"
  | "error"
  | "stopped";

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  status?: MessageStatus;
  model_id?: string | null;
  attachments?: AttachmentRef[];
  created_at?: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  project_id?: string | null;
  created_at?: string;
  updated_at?: string;
  pinned?: boolean;
}

export type AppState =
  | "idle" | "composing" | "sending" | "streaming" | "stopped"
  | "complete" | "listening" | "transcribing" | "speaking"
  | "interrupted" | "error";

export interface GeneratedImage extends ImageResponse {}
export interface ResearchSource { title: string; url: string; snippet: string }
export interface ResearchResult {
  cached: boolean;
  answer?: string;
  sources: ResearchSource[];
  daily_remaining: number;
}
export interface ResearchState { configured: boolean; daily_remaining: number; message?: string }

export interface ProjectFile {
  path: string;
  content: string;
  language?: string;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  instructions: string;
  files?: ProjectFile[];
  preview_url?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  instructions?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  instructions?: string;
  files?: ProjectFile[];
  preview_url?: string | null;
}

export interface SendMessageRequest {
  content: string;
  model_id?: string;
  operation: Operation;
  attachment_ids: string[];
  from_message_id?: string | null;
}

export interface StreamStartEvent {
  user_message?: Message;
  message_id: string;
  provider: string;
  model: string;
  credits?: CreditState;
  operation?: Operation;
}

export interface StreamDeltaEvent {
  message_id: string;
  text: string;
}

export interface StreamDoneEvent {
  message_id: string;
  status: MessageStatus;
  credits?: CreditState;
}

export interface StreamErrorEvent {
  message_id?: string;
  detail: string;
}

export interface StreamCallbacks {
  onStart?: (event: StreamStartEvent) => void;
  onDelta?: (event: StreamDeltaEvent) => void;
  onDone?: (event: StreamDoneEvent) => void;
  onError?: (event: StreamErrorEvent) => void;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: Message[];
}

export interface SearchHit {
  conversation_id: string;
  message_id: string;
  title: string;
  snippet: string;
  created_at?: string;
}

export interface ImageResponse {
  prompt: string;
  data_url: string;
  caption: string;
  message_id?: string | null;
}

export interface WaitlistResponse {
  joined: boolean;
  position: number;
  email: string;
  message: string;
}
