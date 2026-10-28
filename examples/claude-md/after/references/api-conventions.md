# API handler example

The rules are in `CLAUDE.md` under "API". This is the reference shape of a compliant handler; copy it when adding an endpoint.

```ts
import { NextResponse } from "next/server";
import { z } from "zod";
import { requireSession } from "@/lib/auth";
import { db } from "@lumen/db";
import { AppError } from "@/lib/errors";

const Body = z.object({
  text: z.string().min(1).max(280),
  scheduledAt: z.string().datetime(),
  accountId: z.string().cuid(),
});

export async function POST(req: Request) {
  const session = await requireSession();
  const parsed = Body.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: { code: "invalid_body", message: parsed.error.message } }, { status: 400 });
  }
  try {
    const post = await db.post.create({ data: { ...parsed.data, workspaceId: session.workspaceId } });
    return NextResponse.json({ data: post }, { status: 201 });
  } catch (e) {
    const err = AppError.from(e);
    return NextResponse.json({ error: { code: err.code, message: err.message } }, { status: err.status });
  }
}
```
