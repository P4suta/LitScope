import createClient from "openapi-fetch";
// import type { paths } from "./schema";

// TODO: Uncomment after running `bun run generate:api` with the backend running
// export const api = createClient<paths>({ baseUrl: "/api/v1" });

export const api = createClient({ baseUrl: "/api/v1" });
