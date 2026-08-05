import Card from "../common/Card";

function StatisticCard({
    icon,
    title,
    value,
    subtitle
}) {
    return (
        <Card>
            <div className="flex flex-col h-full">

                <div className="mb-4 text-[#A85A24]">
                    {icon}
                </div>

                <h3 className="text-sm font-medium text-gray-500">
                    {title}
                </h3>

                <h1 className="text-3xl font-bold mt-1">
                    {value}
                </h1>

                <p className="text-sm text-orange-400 mt-auto">
                    {subtitle}
                </p>

            </div>
        </Card>
    );
}

export default StatisticCard;