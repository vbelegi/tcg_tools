import { useRef, useState } from "react";

type Props = {
  id: string;
  accept: string;
  disabled?: boolean;
  buttonLabel: string;
  emptyLabel?: string;
  onFile: (file: File) => void;
};

export function FilePicker({
  id,
  accept,
  disabled,
  buttonLabel,
  emptyLabel = "Nenhum arquivo escolhido",
  onFile,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  return (
    <div className="file-picker">
      <input
        ref={inputRef}
        id={id}
        type="file"
        accept={accept}
        disabled={disabled}
        className="visually-hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          setFileName(file.name);
          onFile(file);
          e.target.value = "";
        }}
      />
      <button
        type="button"
        className="secondary"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
      >
        {buttonLabel}
      </button>
      <span className="file-picker-name">{fileName ?? emptyLabel}</span>
    </div>
  );
}
