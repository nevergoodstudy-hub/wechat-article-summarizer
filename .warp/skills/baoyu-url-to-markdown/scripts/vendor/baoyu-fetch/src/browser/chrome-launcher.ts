import { launch, type LaunchedChrome } from "chrome-launcher";
import type { Logger } from "../utils/logger";
import { ensureChromeProfileDir, findExistingChromeDebugPort, resolveChromeProfileDir } from "./profile";

interface ChromeVersionResponse {
  webSocketDebuggerUrl: string;
}

export interface ChromeConnectOptions {
  cdpUrl?: string;
  browserPath?: string;
  headless?: boolean;
  logger?: Logger;
  profileDir?: string;
}

export interface ChromeConnection {
  browserWsUrl: string;
  origin?: string;
  port?: number;
  profileDir?: string;
  launched: boolean;
  close(): Promise<void>;
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

async function connectToHttpEndpoint(origin: string): Promise<ChromeConnection> {
  const normalizedOrigin = origin.replace(/\/$/, "");
  const version = await fetchJson<ChromeVersionResponse>(`${normalizedOrigin}/json/version`);
  return {
    browserWsUrl: version.webSocketDebuggerUrl,
    origin: normalizedOrigin,
    port: Number(new URL(normalizedOrigin).port || 80),
    launched: false,
    async close() {
      // Reused external Chrome, nothing to close here.
    },
  };
}

async function tryReuseChrome(profileDir: string, logger?: Logger): Promise<ChromeConnection | null> {
  const port = await findExistingChromeDebugPort({ profileDir });
  if (!port) {
    return null;
  }

  const origin = `http://127.0.0.1:${port}`;
  try {
    const connection = await connectToHttpEndpoint(origin);
    logger?.info(`Reusing Chrome debugger at ${origin} for profile ${profileDir}`);
    return {
      ...connection,
      profileDir,
    };
  } catch {
    // Debugger disappeared between detection and connect.
  }
  return null;
}

export async function connectChrome(options: ChromeConnectOptions): Promise<ChromeConnection> {
  if (options.cdpUrl) {
    if (options.cdpUrl.startsWith("ws://") || options.cdpUrl.startsWith("wss://")) {
      return {
        browserWsUrl: options.cdpUrl,
        launched: false,
        async close() {},
      };
    }
    return connectToHttpEndpoint(options.cdpUrl);
  }

  const profileDir = ensureChromeProfileDir(resolveChromeProfileDir(options.profileDir));
  const reused = await tryReuseChrome(profileDir, options.logger);
  if (reused) {
    return reused;
  }

  options.logger?.warn(`No running Chrome debugger found for profile ${profileDir}. Launching Chrome with that profile.`);

  const launchedChrome: LaunchedChrome = await launch({
    chromePath: options.browserPath,
    userDataDir: profileDir,
    chromeFlags: [
      "--disable-background-networking",
      "--disable-default-apps",
      "--disable-popup-blocking",
      "--disable-sync",
      "--no-first-run",
      "--no-default-browser-check",
      "--remote-allow-origins=*",
      ...(!options.headless ? ["--no-startup-window"] : []),
      ...(options.headless ? ["--headless=new"] : []),
    ],
  });

  const origin = `http://127.0.0.1:${launchedChrome.port}`;
  const version = await fetchJson<ChromeVersionResponse>(`${origin}/json/version`);

  return {
    browserWsUrl: version.webSocketDebuggerUrl,
    origin,
    port: launchedChrome.port,
    profileDir,
    launched: true,
    async close() {
      launchedChrome.kill();
    },
  };
}
