"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  fetchCurrentUser,
  updateUserPersonalization,
  type User,
} from "@/lib/api/backend-client";

export default function PersonalizationPage() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Form state
  const [nickname, setNickname] = useState("");
  const [occupation, setOccupation] = useState("");
  const [aboutYou, setAboutYou] = useState("");
  const [customInstructions, setCustomInstructions] = useState("");

  useEffect(() => {
    async function loadUser() {
      try {
        const userData = await fetchCurrentUser();
        setUser(userData);
        setNickname(userData.nickname ?? "");
        setOccupation(userData.occupation ?? "");
        setAboutYou(userData.about_you ?? "");
        setCustomInstructions(userData.custom_instructions ?? "");
      } catch (error) {
        console.error("Failed to load user:", error);
        toast.error("Failed to load user settings");
      } finally {
        setIsLoading(false);
      }
    }
    loadUser();
  }, []);

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
    setIsSaving(true);
    try {
      const updatedUser = await updateUserPersonalization({
        nickname: nickname || null,
        occupation: occupation || null,
        about_you: aboutYou || null,
        custom_instructions: customInstructions || null,
      });
      setUser(updatedUser);
      toast.success("Settings saved successfully");
    } catch (error) {
      console.error("Failed to save settings:", error);
      toast.error("Failed to save settings");
    } finally {
      setIsSaving(false);
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
        <h2 className="text-lg font-semibold">Personalization</h2>
        <p className="text-sm text-muted-foreground">
          Customize how the AI interacts with you. These settings help the AI
          provide more relevant and personalized responses.
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <label
            htmlFor="nickname"
            className="text-sm font-medium leading-none"
          >
            Nickname
          </label>
          <Input
            id="nickname"
            placeholder="What should the AI call you?"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            The name the AI will use when addressing you
          </p>
        </div>

        <div className="space-y-2">
          <label
            htmlFor="occupation"
            className="text-sm font-medium leading-none"
          >
            Occupation
          </label>
          <Input
            id="occupation"
            placeholder="e.g., Software Engineer, Teacher, Student"
            value={occupation}
            onChange={(e) => setOccupation(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Helps the AI tailor responses to your professional context
          </p>
        </div>

        <div className="space-y-2">
          <label
            htmlFor="about-you"
            className="text-sm font-medium leading-none"
          >
            About You
          </label>
          <Textarea
            id="about-you"
            placeholder="Tell the AI about yourself, your interests, goals, or anything relevant..."
            value={aboutYou}
            onChange={(e) => setAboutYou(e.target.value)}
            rows={4}
          />
          <p className="text-xs text-muted-foreground">
            Background information to help personalize responses
          </p>
        </div>

        <div className="space-y-2">
          <label
            htmlFor="custom-instructions"
            className="text-sm font-medium leading-none"
          >
            Custom Instructions
          </label>
          <Textarea
            id="custom-instructions"
            placeholder="e.g., Always explain technical concepts simply. Prefer concise answers. Use examples when possible."
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            rows={6}
          />
          <p className="text-xs text-muted-foreground">
            Specific instructions for how the AI should respond to you
          </p>
        </div>
      </div>

      {hasChanges && (
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving && <Loader2 className="size-4 animate-spin mr-2" />}
            Save Changes
          </Button>
        </div>
      )}
    </div>
  );
}
