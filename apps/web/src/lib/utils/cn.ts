import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Combina clases con tailwind-merge (resuelve conflictos de utilidades). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
