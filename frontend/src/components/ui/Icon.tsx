import type { SVGProps } from "react";

/**
 * A small, hand-drawn icon set — deliberately not a generic icon
 * library (Lucide/Heroicons/Feather appear identically in every AI
 * product). Consistent 1.6px stroke, round joins, 20x20 grid. Add new
 * names here rather than reaching for an npm icon package.
 */
export type IconName =
  | "video"
  | "chapters"
  | "transcript"
  | "summary"
  | "translate"
  | "search"
  | "chat"
  | "quiz"
  | "flashcard"
  | "chevron-down"
  | "chevron-right"
  | "chevron-left"
  | "chevron-up"
  | "close"
  | "check"
  | "alert"
  | "info"
  | "upload"
  | "play"
  | "pause"
  | "volume"
  | "volume-mute"
  | "fullscreen"
  | "skip-back"
  | "skip-forward"
  | "logout"
  | "user"
  | "plus"
  | "more"
  | "download"
  | "copy"
  | "refresh"
  | "clock"
  | "spinner"
  | "eye"
  | "eye-off"
  | "trash"
  | "arrow-left"
  | "empty-inbox"
  | "wifi-off"
  | "lock"
  | "server-off"
  | "file-warning";

const paths: Record<IconName, JSX.Element> = {
  video: (
    <>
      <rect x="2" y="5" width="12" height="10" rx="2" />
      <path d="M14 8.5 18.2 6a.9.9 0 0 1 1.3.8v6.4a.9.9 0 0 1-1.3.8L14 11.5" />
    </>
  ),
  chapters: (
    <>
      <path d="M3 5h10" />
      <path d="M3 10h14" />
      <path d="M3 15h7" />
      <circle cx="17" cy="15" r="2.2" />
    </>
  ),
  transcript: (
    <>
      <path d="M5 3h7l4 4v10a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M7 10h6M7 13h6M7 7h3" />
    </>
  ),
  summary: (
    <>
      <path d="M4 4h12" />
      <path d="M4 8h12" />
      <path d="M4 12h8" />
      <path d="M4 16h5" />
    </>
  ),
  translate: (
    <>
      <path d="M3 5h7" />
      <path d="M6.5 3.5v2.2C6.5 9 5 11 3 12" />
      <path d="M4.3 9.2c1 1.4 3 2.6 4.7 3" />
      <path d="M12 17l3.2-8 3.3 8" />
      <path d="M12.9 14.6h4.6" />
    </>
  ),
  search: (
    <>
      <circle cx="9" cy="9" r="6" />
      <path d="m17 17-4-4" />
    </>
  ),
  chat: (
    <>
      <path d="M3 5.5A2.5 2.5 0 0 1 5.5 3h9A2.5 2.5 0 0 1 17 5.5v6A2.5 2.5 0 0 1 14.5 14H9l-4 3v-3H5.5A2.5 2.5 0 0 1 3 11.5Z" />
    </>
  ),
  quiz: (
    <>
      <circle cx="10" cy="10" r="7.2" />
      <path d="M7.7 7.8a2.3 2.3 0 1 1 3.3 2.1c-.7.4-1 .7-1 1.5" />
      <circle cx="10" cy="13.9" r="0.15" fill="currentColor" stroke="none" />
    </>
  ),
  flashcard: (
    <>
      <rect x="2.5" y="4" width="15" height="10" rx="1.6" />
      <path d="M2.5 8h15" />
    </>
  ),
  "chevron-down": <path d="m5 7.5 5 5 5-5" />,
  "chevron-right": <path d="m7.5 5 5 5-5 5" />,
  "chevron-left": <path d="m12.5 5-5 5 5 5" />,
  "chevron-up": <path d="m5 12.5 5-5 5 5" />,
  close: <path d="M5 5l10 10M15 5 5 15" />,
  check: <path d="M4 10.5 8 14.5 16 5.5" />,
  alert: (
    <>
      <path d="M10 2.5 18 16.5H2Z" />
      <path d="M10 8v3.4" />
      <path d="M10 13.8v.1" />
    </>
  ),
  info: (
    <>
      <circle cx="10" cy="10" r="7.2" />
      <path d="M10 9.3v4.4" />
      <path d="M10 6.8v.1" />
    </>
  ),
  upload: (
    <>
      <path d="M10 13V3.5" />
      <path d="m6 7.2 4-4 4 4" />
      <path d="M4 13.5v1.8A1.7 1.7 0 0 0 5.7 17h8.6a1.7 1.7 0 0 0 1.7-1.7v-1.8" />
    </>
  ),
  play: <path d="M6 4.2v11.6a.7.7 0 0 0 1.1.6l9-5.8a.7.7 0 0 0 0-1.2l-9-5.8A.7.7 0 0 0 6 4.2Z" />,
  pause: (
    <>
      <rect x="5.5" y="4" width="3.2" height="12" rx="0.8" />
      <rect x="11.3" y="4" width="3.2" height="12" rx="0.8" />
    </>
  ),
  volume: (
    <>
      <path d="M3 8v4h3l4 3.3V4.7L6 8Z" />
      <path d="M13.2 7a4 4 0 0 1 0 6" />
      <path d="M15.4 4.8a7.3 7.3 0 0 1 0 10.4" />
    </>
  ),
  "volume-mute": (
    <>
      <path d="M3 8v4h3l4 3.3V4.7L6 8Z" />
      <path d="m13 7.5 4 5M17 7.5l-4 5" />
    </>
  ),
  fullscreen: (
    <>
      <path d="M3 7V4.6A1.6 1.6 0 0 1 4.6 3H7" />
      <path d="M13 3h2.4A1.6 1.6 0 0 1 17 4.6V7" />
      <path d="M17 13v2.4a1.6 1.6 0 0 1-1.6 1.6H13" />
      <path d="M7 17H4.6A1.6 1.6 0 0 1 3 15.4V13" />
    </>
  ),
  "skip-back": (
    <>
      <path d="M4 4.5v11" />
      <path d="M16 5.2 8 10l8 4.8Z" />
    </>
  ),
  "skip-forward": (
    <>
      <path d="M16 4.5v11" />
      <path d="M4 5.2 12 10l-8 4.8Z" />
    </>
  ),
  logout: (
    <>
      <path d="M8 3H4.6A1.6 1.6 0 0 0 3 4.6v10.8A1.6 1.6 0 0 0 4.6 17H8" />
      <path d="M13 13.5 17 10l-4-3.5" />
      <path d="M17 10H7.5" />
    </>
  ),
  user: (
    <>
      <circle cx="10" cy="6.5" r="3.2" />
      <path d="M3.5 17c1-3.5 3.8-5.3 6.5-5.3s5.5 1.8 6.5 5.3" />
    </>
  ),
  plus: <path d="M10 4v12M4 10h12" />,
  more: (
    <>
      <circle cx="4.5" cy="10" r="1" fill="currentColor" stroke="none" />
      <circle cx="10" cy="10" r="1" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="10" r="1" fill="currentColor" stroke="none" />
    </>
  ),
  download: (
    <>
      <path d="M10 3v9.5" />
      <path d="m6 8.7 4 4 4-4" />
      <path d="M4 14.5v1.8A1.7 1.7 0 0 0 5.7 18h8.6a1.7 1.7 0 0 0 1.7-1.7v-1.8" />
    </>
  ),
  copy: (
    <>
      <rect x="7.5" y="7.5" width="9.5" height="9.5" rx="1.6" />
      <path d="M4.8 12.5H4A1.6 1.6 0 0 1 2.4 11V4A1.6 1.6 0 0 1 4 2.4h7a1.6 1.6 0 0 1 1.6 1.6v.8" />
    </>
  ),
  refresh: (
    <>
      <path d="M16 10a6 6 0 1 1-2-4.5" />
      <path d="M16 3v3.5h-3.5" />
    </>
  ),
  clock: (
    <>
      <circle cx="10" cy="10" r="7.2" />
      <path d="M10 6v4.3l3 1.9" />
    </>
  ),
  spinner: (
    <>
      <path d="M10 3a7 7 0 1 0 7 7" />
    </>
  ),
  eye: (
    <>
      <path d="M2 10s2.7-5 8-5 8 5 8 5-2.7 5-8 5-8-5-8-5Z" />
      <circle cx="10" cy="10" r="2.3" />
    </>
  ),
  "eye-off": (
    <>
      <path d="M3.5 3.5l13 13" />
      <path d="M8.6 5.3A8.6 8.6 0 0 1 10 5c5.3 0 8 5 8 5a13.6 13.6 0 0 1-3 3.5M6 6.6C3.5 8 2 10 2 10s2.7 5 8 5c1 0 1.9-.2 2.7-.4" />
      <path d="M8.1 8.1a2.3 2.3 0 0 0 3.2 3.3" />
    </>
  ),
  trash: (
    <>
      <path d="M3.5 5.5h13" />
      <path d="M7 5.5v-1a1.4 1.4 0 0 1 1.4-1.4h3.2A1.4 1.4 0 0 1 13 4.5v1" />
      <path d="M5.5 5.5 6.2 16a1.4 1.4 0 0 0 1.4 1.3h4.8a1.4 1.4 0 0 0 1.4-1.3l.7-10.5" />
      <path d="M8.3 8.7v5M11.7 8.7v5" />
    </>
  ),
  "arrow-left": <path d="M16 10H4m0 0 5-5m-5 5 5 5" />,
  "empty-inbox": (
    <>
      <path d="M3 11.5 5.2 4h9.6l2.2 7.5" />
      <path d="M3 11.5h4.3a2.7 2.7 0 0 0 2.6 2h.2a2.7 2.7 0 0 0 2.6-2H17v3.8A1.7 1.7 0 0 1 15.3 17H4.7A1.7 1.7 0 0 1 3 15.3Z" />
    </>
  ),
  "wifi-off": (
    <>
      <path d="M2.5 2.5l15 15" />
      <path d="M5 8.3a10 10 0 0 1 3-1.8M12 6.5a10 10 0 0 1 3 1.8" />
      <path d="M7.5 11a5.4 5.4 0 0 1 2.5-.7c.7 0 1.4.1 2 .4M10 14v.1" />
    </>
  ),
  lock: (
    <>
      <rect x="4" y="9" width="12" height="8" rx="1.6" />
      <path d="M6.5 9V6.5a3.5 3.5 0 0 1 7 0V9" />
    </>
  ),
  "server-off": (
    <>
      <rect x="3" y="4" width="14" height="5.5" rx="1.4" />
      <rect x="3" y="11" width="14" height="5.5" rx="1.4" />
      <path d="M6 6.8h.01M6 13.8h.01" />
    </>
  ),
  "file-warning": (
    <>
      <path d="M6 3h5l4 4v9a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M10 9v3" />
      <path d="M10 14.2v.1" />
    </>
  ),
};

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 20, className, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      {paths[name]}
    </svg>
  );
}
