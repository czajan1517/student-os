import Card from "../common/Card";

function StatisticCard({
    icon,
    title,
    value,
    subtitle,
    subtitleClassName = "text-[#B85E1B]",
    progress,
}) {
    const safeProgress = Math.min(100, Math.max(0, progress ?? 0));

    return (
        <Card className="h-[166px] border border-[#EEE7E1] p-5! shadow-[0_2px_10px_rgba(77,50,32,0.05)]">
            <div className="flex h-full min-w-0 items-start gap-4">
                <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-[#FFF0E5] text-[#C7651E]">
                    {icon}
                </div>

                <div className="flex h-full min-w-0 flex-1 flex-col pt-0.5">
                    <h3 className="whitespace-nowrap text-base font-semibold leading-6 text-[#241C17]">
                        {title}
                    </h3>

                    <p className="mt-2 text-[1.85rem] font-semibold leading-none tracking-[-0.025em] text-black">
                        {value}
                    </p>

                    <div className="mt-auto min-w-0">
                        <p className={`truncate text-sm leading-5 ${subtitleClassName}`}>
                            {subtitle}
                        </p>

                        {progress !== undefined && (
                            <div
                                className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#F0EEEB]"
                                role="progressbar"
                                aria-label={`${title} completion`}
                                aria-valuemin="0"
                                aria-valuemax="100"
                                aria-valuenow={Math.round(safeProgress)}
                            >
                                <div
                                    className="h-full rounded-full bg-linear-to-r from-[#E96D1F] to-[#FFB56E]"
                                    style={{ width: `${safeProgress}%` }}
                                />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Card>
    );
}

export default StatisticCard;
