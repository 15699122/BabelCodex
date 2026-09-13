import { describe, expect, it } from "vitest";
import { assertCompatibleServerInfo, PROTOCOL_VERSION } from "./protocol";
import type { ServerInfo } from "./protocol";

const serverInfo = (overrides: Partial<ServerInfo> = {}): ServerInfo => ({
  protocol_version: PROTOCOL_VERSION,
  package_version: "0.1.0",
  capabilities: ["start_translation", "shutdown"],
  ...overrides,
});

describe("assertCompatibleServerInfo", () => {
  it("accepts a sidecar speaking the expected protocol version", () => {
    expect(() => assertCompatibleServerInfo(serverInfo())).not.toThrow();
  });

  it("rejects a stale sidecar with a rebuild hint", () => {
    try {
      assertCompatibleServerInfo(serverInfo({ protocol_version: PROTOCOL_VERSION - 1 }));
      expect.unreachable("stale sidecar must be rejected");
    } catch (error) {
      expect((error as Error).message).toMatch(/sidecar protocol mismatch/);
      expect((error as Error).message).toMatch(/Rebuild the bundled babelcodex-service/);
    }
  });
});
