"use client";

import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: string;
  /**
   * A mutation failure from the action this dialog just confirmed -
   * rendered as a real, distinctly-styled alert (same pattern as
   * login/register's formError) rather than silently closing the
   * dialog on failure, which previously left no visible sign the
   * action didn't actually happen.
   */
  error?: string | null;
  confirmLabel?: string;
  isConfirming?: boolean;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  description,
  error,
  confirmLabel = "Confirm",
  isConfirming,
  danger,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      title={title}
      description={description}
      width="sm"
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant={danger ? "danger" : "primary"}
            size="sm"
            onClick={onConfirm}
            isLoading={isConfirming}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      {error && (
        <p role="alert" className="border-l-2 border-error bg-error-muted px-3 py-2 text-body-sm text-error">
          {error}
        </p>
      )}
    </Dialog>
  );
}
