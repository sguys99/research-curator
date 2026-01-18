import { useToastStore } from "@/stores/toast-store";

export const useToast = () => {
  const addToast = useToastStore((state) => state.addToast);
  const removeToast = useToastStore((state) => state.removeToast);

  return {
    toast: addToast,
    dismiss: removeToast,
  };
};
