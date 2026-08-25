import * as React from 'react';
import { Button, ModalBody, ModalFooter, ModalHeader, ModalVariant } from '@patternfly/react-core';
import { ChatbotDisplayMode, ChatbotModal } from '@patternfly/chatbot';

interface CameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
}

const CameraModal: React.FunctionComponent<CameraModalProps> = ({ isOpen, onClose, onCapture }) => {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const canvasRef = React.useRef<HTMLCanvasElement>(null);
  const streamRef = React.useRef<MediaStream | undefined>(undefined);
  const [error, setError] = React.useState<string>();

  React.useEffect(() => {
    if (!isOpen) return undefined;
    navigator.mediaDevices?.getUserMedia({ video: { facingMode: 'environment' } })
      .then((stream) => {
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(() => setError('Unable to access the camera. Check browser permission and HTTPS.'));
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = undefined;
      setError(undefined);
    };
  }, [isOpen]);

  const capture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !video.videoWidth) return;
    const scale = Math.min(1, 1600 / video.videoWidth);
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) return;
      onCapture(new File([blob], `photo-${Date.now()}.jpg`, { type: 'image/jpeg' }));
      onClose();
    }, 'image/jpeg', 0.85);
  };

  return (
    <ChatbotModal
      title="Take a picture"
      isOpen={isOpen}
      onClose={onClose}
      variant={ModalVariant.small}
      displayMode={ChatbotDisplayMode.embedded}
    >
      <ModalHeader title="Add a picture to the question" />
      <ModalBody>
        {error ? <div>{error}</div> : <video ref={videoRef} autoPlay playsInline className="camera-preview" />}
        <canvas ref={canvasRef} hidden />
      </ModalBody>
      <ModalFooter>
        <Button variant="primary" onClick={capture} isDisabled={Boolean(error)}>Take picture</Button>
        <Button variant="link" onClick={onClose}>Cancel</Button>
      </ModalFooter>
    </ChatbotModal>
  );
};

export default CameraModal;
