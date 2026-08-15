function Quotecard({
    quote = "Discipline is the bridge between goals and accomplishment.",
    author = "Jim Rohn",
}) {
    return (
        <figure className="flex min-h-24 w-full items-center gap-5 rounded-xl border border-[#F3E2D3] bg-[#FFF2E7] px-7 py-6 shadow-[0_2px_10px_rgba(77,50,32,0.04)]">
            <span
                className="-mt-2 shrink-0 font-serif text-6xl font-bold leading-none text-[#C7651E]"
                aria-hidden="true"
            >
                “
            </span>

            <div className="min-w-0">
                <blockquote className="text-[0.95rem] font-medium leading-6 text-[#30251F]">
                    {quote}
                </blockquote>

                {author && (
                    <figcaption className="mt-1 text-sm font-medium text-[#B85E1B]">
                        – {author}
                    </figcaption>
                )}
            </div>
        </figure>
    );
}

export default Quotecard;
