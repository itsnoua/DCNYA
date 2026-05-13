export const Utils = {
    animateValue(id, start, end, duration) {
        const obj = document.getElementById(id);
        if (!obj) return;
        const range = end - start;
        let current = start;
        const increment = end > start ? Math.ceil(range / (duration / 16)) : Math.floor(range / (duration / 16));
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                obj.innerText = end.toLocaleString();
                clearInterval(timer);
            } else {
                obj.innerText = current.toLocaleString();
            }
        }, 16);
    }
};
