import { type RefObject, useCallback, useEffect } from "react";

/**
 * 지정된 요소 외부 클릭 시 콜백 함수를 실행하는 커스텀 훅
 *
 * @param ref - 클릭 감지 대상 요소의 RefObject
 * @param callback - 외부 클릭 시 실행할 콜백 함수
 * @param enabled - 훅 활성화 여부 (기본값: true)
 */
export const useClickOutside = <T extends HTMLElement>(
  ref: RefObject<T | null>,
  callback: () => void,
  enabled = true,
) => {
  const handleClickOutside = useCallback(
    (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    },
    [ref, callback],
  );

  useEffect(() => {
    if (!enabled) {
      return;
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [enabled, handleClickOutside]);
};
