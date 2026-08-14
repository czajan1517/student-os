import { ArrowRight, CalendarDays } from "lucide-react";
import { NavLink } from "react-router-dom";
import Card from "../common/Card";

const HOUR_HEIGHT = 80;
const MINUTES_IN_HOUR = 60;
const DEFAULT_START_HOUR = 8;
const DEFAULT_VISIBLE_HOURS = 7;

function formatTime(date) {
    return date.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
    });
}

function formatHour(totalMinutes) {
    const date = new Date();
    const minutesInDay = 24 * MINUTES_IN_HOUR;
    const normalizedMinutes =
        ((totalMinutes % minutesInDay) + minutesInDay) % minutesInDay;

    date.setHours(Math.floor(normalizedMinutes / MINUTES_IN_HOUR));
    date.setMinutes(normalizedMinutes % MINUTES_IN_HOUR, 0, 0);

    return date.toLocaleTimeString([], { hour: "numeric" });
}

function minutesFromStartOfDay(date) {
    return (
        date.getHours() * MINUTES_IN_HOUR +
        date.getMinutes() +
        date.getSeconds() / MINUTES_IN_HOUR
    );
}

function isSameEvent(event, nextEvent) {
    if (!nextEvent) {
        return false;
    }

    if (event.id != null && nextEvent.id != null) {
        return event.id === nextEvent.id;
    }

    return (
        event.start_date === nextEvent.start_date &&
        event.end_date === nextEvent.end_date &&
        event.title === nextEvent.title
    );
}

function Schedulepanel({ events = [], nextEvent = null }) {
    const validEvents = events
        .map((event) => ({
            ...event,
            start: new Date(event.start_date),
            end: new Date(event.end_date),
        }))
        .filter(
            (event) =>
                !Number.isNaN(event.start.getTime()) &&
                !Number.isNaN(event.end.getTime()) &&
                event.end > event.start
        )
        .sort((a, b) => a.start - b.start);

    const earliestStart = validEvents[0]?.start;
    const latestEndMinute = validEvents.reduce(
        (latest, event) =>
            Math.max(
                latest,
                minutesFromStartOfDay(event.start) +
                    (event.end - event.start) / (60 * 1000)
            ),
        0
    );

    const timelineStart = earliestStart
        ? Math.floor(
              (minutesFromStartOfDay(earliestStart) - MINUTES_IN_HOUR) /
                  MINUTES_IN_HOUR
          ) * MINUTES_IN_HOUR
        : DEFAULT_START_HOUR * MINUTES_IN_HOUR;
    const timelineEnd = validEvents.length
        ? Math.max(
              Math.ceil(
                  (latestEndMinute + MINUTES_IN_HOUR) / MINUTES_IN_HOUR
              ) * MINUTES_IN_HOUR,
              timelineStart + DEFAULT_VISIBLE_HOURS * MINUTES_IN_HOUR
          )
        : timelineStart + DEFAULT_VISIBLE_HOURS * MINUTES_IN_HOUR;
    const timelineHeight =
        ((timelineEnd - timelineStart) / MINUTES_IN_HOUR) * HOUR_HEIGHT;
    const hourMarkers = Array.from(
        { length: (timelineEnd - timelineStart) / MINUTES_IN_HOUR + 1 },
        (_, index) => timelineStart + index * MINUTES_IN_HOUR
    );

    return (
        <Card className="overflow-hidden border border-[#EEE7E1] p-0! shadow-[0_2px_10px_rgba(77,50,32,0.05)]">
            <div className="flex items-center justify-between border-b border-[#EEE7E1] px-6 py-4">
                <div className="flex items-center gap-3">
                    <span className="flex size-10 items-center justify-center rounded-full bg-[#FFF0E5] text-[#C7651E]">
                        <CalendarDays size={21} strokeWidth={1.8} />
                    </span>
                    <div>
                        <h2 className="text-xl font-semibold text-[#241C17]">
                            Today's Schedule
                        </h2>
                        <p className="text-sm text-[#7C7068]">
                            {validEvents.length
                                ? `${validEvents.length} ${validEvents.length === 1 ? "event" : "events"} today`
                                : "Your day is open"}
                        </p>
                    </div>
                </div>

                <NavLink
                    to="/calendar"
                    className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-[#C7651E] transition-colors hover:bg-[#FFF0E5] hover:text-[#9E4812] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#C7651E]"
                >
                    View calendar
                    <ArrowRight size={16} aria-hidden="true" />
                </NavLink>
            </div>

            <div
                className="h-[350px] overflow-y-auto overscroll-contain"
                aria-label="Today's calendar timeline"
            >
                <div
                    className="relative min-w-[30rem] bg-white"
                    style={{ height: `${timelineHeight}px` }}
                >
                    <div className="absolute inset-y-0 left-0 w-24 border-r border-[#EDE5DE] bg-[#FFFBF8]" />

                    {hourMarkers.map((minute) => {
                        const top =
                            ((minute - timelineStart) / MINUTES_IN_HOUR) *
                            HOUR_HEIGHT;

                        return (
                            <div
                                key={minute}
                                className="absolute right-0 left-0 border-t border-[#EFE9E4]"
                                style={{ top: `${top}px` }}
                            >
                                <span className="absolute top-0 left-4 w-16 -translate-y-1/2 bg-[#FFFBF8] pr-2 text-right text-xs font-medium text-[#82766E]">
                                    {formatHour(minute)}
                                </span>
                            </div>
                        );
                    })}

                    {validEvents.map((event) => {
                        const startMinute = minutesFromStartOfDay(event.start);
                        const durationMinutes =
                            (event.end - event.start) / (60 * 1000);
                        const top =
                            ((startMinute - timelineStart) / MINUTES_IN_HOUR) *
                            HOUR_HEIGHT;
                        const durationHeight =
                            (durationMinutes / MINUTES_IN_HOUR) * HOUR_HEIGHT;
                        const highlighted = isSameEvent(event, nextEvent);

                        return (
                            <div
                                key={`${event.id ?? event.title}-${event.start_date}`}
                                className="absolute right-3 left-0 z-10"
                                style={{
                                    top: `${top}px`,
                                    height: `${durationHeight}px`,
                                }}
                            >
                                <div
                                    className={`absolute inset-y-0 left-0 w-24 border-r-4 ${
                                        highlighted
                                            ? "border-[#C75A15] bg-[#F7A261]/55"
                                            : "border-[#E8A16B] bg-[#FCE3D0]/70"
                                    }`}
                                    aria-hidden="true"
                                />

                                <div
                                    className={`absolute top-0 right-0 left-[6.75rem] flex min-h-7 items-center justify-between gap-3 overflow-hidden rounded-lg border-l-4 px-3 shadow-sm ${
                                        highlighted
                                            ? "border-[#C75A15] bg-[#FDE7D4] text-[#6F2F0C] ring-1 ring-[#F1BC91]"
                                            : "border-[#E89A60] bg-[#FFF4EB] text-[#513C2F]"
                                    }`}
                                    style={{ height: `${Math.max(durationHeight - 4, 28)}px` }}
                                >
                                    <div className="flex min-w-0 items-center gap-2">
                                        {highlighted && (
                                            <span className="shrink-0 rounded-full bg-[#C75A15] px-2 py-0.5 text-[0.65rem] font-bold uppercase tracking-wide text-white">
                                                Next up
                                            </span>
                                        )}
                                        <p className="truncate text-sm font-semibold">
                                            {event.title || "Untitled event"}
                                        </p>
                                    </div>

                                    <p className="shrink-0 text-xs font-medium opacity-80">
                                        {formatTime(event.start)} – {formatTime(event.end)}
                                    </p>
                                </div>
                            </div>
                        );
                    })}

                    {validEvents.length === 0 && (
                        <div className="absolute top-24 right-8 left-32 flex flex-col items-center rounded-xl border border-dashed border-[#E6D8CD] bg-[#FFFCFA] px-5 py-8 text-center">
                            <CalendarDays
                                size={26}
                                strokeWidth={1.7}
                                className="mb-2 text-[#D97825]"
                            />
                            <p className="font-semibold text-[#3D3028]">
                                No events scheduled today
                            </p>
                            <p className="mt-1 text-sm text-[#82766E]">
                                Enjoy the extra space or plan something new.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </Card>
    );
}

export default Schedulepanel;
