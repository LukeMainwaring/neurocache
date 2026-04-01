"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useMyself, useUpdateMyPersonalization } from "@/api/hooks/users";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function PersonalizationPage() {
  const { data: user, isLoading } = useMyself();
  const { updatePersonalization, isPending } = useUpdateMyPersonalization();

  const [nickname, setNickname] = useState("");
  const [occupation, setOccupation] = useState("");
  const [aboutYou, setAboutYou] = useState("");
  const [customInstructions, setCustomInstructions] = useState("");

  // Sync form state when user data loads
  useEffect(() => {
    if (user) {
      setNickname(user.nickname ?? "");
      setOccupation(user.occupation ?? "");
      setAboutYou(user.about_you ?? "");
      setCustomInstructions(user.custom_instructions ?? "");
    }
  }, [user]);

  const hasChanges =
    nickname !== (user?.nickname ?? "") ||
    occupation !== (user?.occupation ?? "") ||
    aboutYou !== (user?.about_you ?? "") ||
    customInstructions !== (user?.custom_instructions ?? "");

  function handleCancel() {
    setNickname(user?.nickname ?? "");
    setOccupation(user?.occupation ?? "");
    setAboutYou(user?.about_you ?? "");
    setCustomInstructions(user?.custom_instructions ?? "");
  }

  async function handleSave() {
    try {
      await updatePersonalization({
        nickname: nickname || null,
        occupation: occupation || null,
        about_you: aboutYou || null,
        custom_instructions: customInstructions || null,
      });
      toast.success("Settings saved successfully");
    } catch (error) {
      console.error("Failed to save settings:", error);
      toast.error("Failed to save settings");
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h2 className="font-semibold text-lg">Personalization</h2>
        <p className="text-muted-foreground text-sm">
          Customize how the AI interacts with you. These settings help the AI
          provide more relevant and personalized responses.
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <label
            className="font-medium text-sm leading-none"
            htmlFor="nickname"
          >
            Nickname
          </label>
          <Input
            id="nickname"
            onChange={(e) => setNickname(e.target.value)}
            placeholder="What should the AI call you?"
            value={nickname}
          />
          <p className="text-muted-foreground text-xs">
            The name the AI will use when addressing you
          </p>
        </div>

        <div className="space-y-2">
          <label
            className="font-medium text-sm leading-none"
            htmlFor="occupation"
          >
            Occupation
          </label>
          <Input
            id="occupation"
            onChange={(e) => setOccupation(e.target.value)}
            placeholder="e.g., Software Engineer, Teacher, Student"
            value={occupation}
          />
          <p className="text-muted-foreground text-xs">
            Helps the AI tailor responses to your professional context
          </p>
        </div>

        <div className="space-y-2">
          <label
            className="font-medium text-sm leading-none"
            htmlFor="about-you"
          >
            About You
          </label>
          <Textarea
            id="about-you"
            onChange={(e) => setAboutYou(e.target.value)}
            placeholder="Tell the AI about yourself, your interests, goals, or anything relevant..."
            rows={4}
            value={aboutYou}
          />
          <p className="text-muted-foreground text-xs">
            Background information to help personalize responses
          </p>
        </div>

        <div className="space-y-2">
          <label
            className="font-medium text-sm leading-none"
            htmlFor="custom-instructions"
          >
            Custom Instructions
          </label>
          <Textarea
            id="custom-instructions"
            onChange={(e) => setCustomInstructions(e.target.value)}
            placeholder="e.g., Always explain technical concepts simply. Prefer concise answers. Use examples when possible."
            rows={6}
            value={customInstructions}
          />
          <p className="text-muted-foreground text-xs">
            Specific instructions for how the AI should respond to you
          </p>
        </div>
      </div>

      {hasChanges && (
        <div className="flex justify-end gap-2">
          <Button disabled={isPending} onClick={handleCancel} variant="outline">
            Cancel
          </Button>
          <Button disabled={isPending} onClick={handleSave}>
            {isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
            Save Changes
          </Button>
        </div>
      )}
    </div>
  );
}
