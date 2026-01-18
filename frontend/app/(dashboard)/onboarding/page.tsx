import OnboardingChat from "@/components/onboarding/OnboardingChat";
import OnboardingSidebar from "@/components/onboarding/OnboardingSidebar";

export default function OnboardingPage() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
      <OnboardingChat />
      <OnboardingSidebar />
    </div>
  );
}
