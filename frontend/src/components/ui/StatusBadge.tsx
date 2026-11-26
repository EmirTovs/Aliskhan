function Status({ value }: { value: string }) {
  const map: Record<string, [string, string]> = {
    accepted: ["Принята", "green"],
    pending: ["Ожидает", "amber"],
    rejected: ["Отклонена", "red"],
    draft: ["Черновик", "slate"],
    planned: ["Запланировано", "blue"],
    in_progress: ["В работе", "blue"],
    completed: ["Завершено", "green"],
    cancelled: ["Отменено", "red"],
  };
  const [label, color] = map[value] || [value, "slate"];
  return (
    <span className={`status ${color}`}>
      <i />
      {label}
    </span>
  );
}
export default Status;
