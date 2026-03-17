"use client";

import { Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useActivateMyself, useMyself } from "@/api/hooks/users";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface ActivationGuardProps {
  children: React.ReactNode;
}

export function ActivationGuard({ children }: ActivationGuardProps) {
  const { data: user, isLoading, error } = useMyself();
  const { activate, isPending } = useActivateMyself();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
          <p className="text-muted-foreground text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4">
        <p className="text-destructive text-sm">
          Something went wrong loading your account.
        </p>
        <Button onClick={() => window.location.reload()} variant="outline">
          Retry
        </Button>
      </div>
    );
  }

  if (user && !user.is_activated) {
    const canSubmit = firstName.trim().length > 0 && lastName.trim().length > 0;

    async function handleSubmit(e: React.FormEvent) {
      e.preventDefault();
      if (!canSubmit) return;
      try {
        await activate({
          first_name: firstName.trim(),
          last_name: lastName.trim(),
        });
      } catch {
        toast.error("Failed to activate account. Please try again.");
      }
    }

    return (
      <div className="flex h-screen items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Welcome to Neurocache</CardTitle>
            <CardDescription>Enter your name to get started</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label
                  className="font-medium text-sm leading-none"
                  htmlFor="first-name"
                >
                  First Name
                </label>
                <Input
                  autoFocus
                  id="first-name"
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="First name"
                  value={firstName}
                />
              </div>
              <div className="space-y-2">
                <label
                  className="font-medium text-sm leading-none"
                  htmlFor="last-name"
                >
                  Last Name
                </label>
                <Input
                  id="last-name"
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Last name"
                  value={lastName}
                />
              </div>
              <Button
                className="w-full"
                disabled={!canSubmit || isPending}
                type="submit"
              >
                {isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
                Get Started
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
