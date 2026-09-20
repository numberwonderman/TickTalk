import { Capacitor } from "@capacitor/core";
import { Camera, CameraResultType, CameraSource } from "@capacitor/camera";

/**
 * Native camera/gallery capture when running inside the Capacitor shell
 * (installed app), falling back to the browser's own file input when
 * running as a plain web page (npm run dev, or the web build viewed in a
 * browser) -- see UploadForm.tsx for the fallback. Returns null on web,
 * where the caller should just use the existing <input type="file">
 * instead of this path.
 */
export async function isNativeCameraAvailable(): Promise<boolean> {
  return Capacitor.isNativePlatform();
}

export async function captureOrPickPhoto(): Promise<File | null> {
  if (!Capacitor.isNativePlatform()) {
    return null;
  }

  const photo = await Camera.getPhoto({
    resultType: CameraResultType.Uri,
    source: CameraSource.Prompt, // lets the user choose camera vs. gallery
    quality: 80,
    allowEditing: false,
  });

  if (!photo.webPath) {
    throw new Error("Camera capture returned no image path");
  }

  const response = await fetch(photo.webPath);
  const blob = await response.blob();
  const extension = photo.format || "jpeg";
  return new File([blob], `ticktalk-capture.${extension}`, {
    type: blob.type || `image/${extension}`,
  });
}
