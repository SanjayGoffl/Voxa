"use client";

import { useEffect, useState } from "react";
import { ArrowBigUp, CornerDownRight } from "lucide-react";
import { api, type Comment } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import Link from "next/link";

export function CommentsSection({ productId }: { productId: string }) {
  const { user } = useAuth();
  const [comments, setComments] = useState<Comment[] | null>(null);
  const [draft, setDraft] = useState("");
  const [posting, setPosting] = useState(false);

  function reload() {
    api.getComments(productId).then(setComments);
  }

  useEffect(() => {
    reload();
  }, [productId]);

  async function submit() {
    if (!draft.trim()) return;
    setPosting(true);
    try {
      await api.postComment(productId, draft);
      setDraft("");
      reload();
    } finally {
      setPosting(false);
    }
  }

  return (
    <Card className="space-y-4">
      <h2 className="font-medium">Discussion</h2>

      {user ? (
        <div className="space-y-2">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Share your experience with this product..."
            rows={3}
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 text-sm"
          />
          <Button onClick={submit} disabled={posting || !draft.trim()}>
            Post comment
          </Button>
        </div>
      ) : (
        <div className="rounded-lg bg-[var(--accent-soft)] p-3 text-sm">
          <Link href="/login" className="text-[var(--accent)] font-medium">
            Log in
          </Link>{" "}
          to join the discussion.
        </div>
      )}

      <div className="space-y-3">
        {comments === null && <div className="text-sm text-muted">Loading comments&hellip;</div>}
        {comments?.length === 0 && (
          <div className="text-sm text-muted">No comments yet &mdash; be the first.</div>
        )}
        {comments?.map((c) => (
          <CommentNode key={c.id} comment={c} productId={productId} onChanged={reload} depth={0} />
        ))}
      </div>
    </Card>
  );
}

function CommentNode({
  comment,
  productId,
  onChanged,
  depth,
}: {
  comment: Comment;
  productId: string;
  onChanged: () => void;
  depth: number;
}) {
  const { user } = useAuth();
  const [replying, setReplying] = useState(false);
  const [draft, setDraft] = useState("");

  async function upvote() {
    if (!user) return;
    await api.upvoteComment(productId, comment.id);
    onChanged();
  }

  async function submitReply() {
    if (!draft.trim()) return;
    await api.postComment(productId, draft, comment.id);
    setDraft("");
    setReplying(false);
    onChanged();
  }

  return (
    <div className={depth > 0 ? "ml-6 border-l border-[var(--border)] pl-4" : ""}>
      <div className="rounded-lg border border-[var(--border)] p-3 text-sm">
        <div className="flex items-center gap-2 text-xs text-muted">
          <span className="font-medium text-[var(--foreground)]">{comment.author_name}</span>
          <span>&middot;</span>
          <span>{new Date(comment.created_at).toLocaleDateString()}</span>
        </div>
        <div className="mt-1.5">{comment.text}</div>
        <div className="mt-2 flex items-center gap-3 text-xs text-muted">
          <button onClick={upvote} className="flex items-center gap-1 hover:text-[var(--accent)]" disabled={!user}>
            <ArrowBigUp size={14} /> {comment.upvotes}
          </button>
          {user && (
            <button onClick={() => setReplying((r) => !r)} className="flex items-center gap-1 hover:text-[var(--accent)]">
              <CornerDownRight size={14} /> Reply
            </button>
          )}
        </div>
        {replying && (
          <div className="mt-2 space-y-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={2}
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] p-2 text-sm"
            />
            <Button variant="outline" onClick={submitReply} disabled={!draft.trim()}>
              Reply
            </Button>
          </div>
        )}
      </div>
      {comment.replies.length > 0 && (
        <div className="mt-2 space-y-2">
          {comment.replies.map((r) => (
            <CommentNode key={r.id} comment={r} productId={productId} onChanged={onChanged} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
