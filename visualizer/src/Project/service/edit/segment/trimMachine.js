import { assign, Machine, send } from 'xstate';
import { fromEventBus } from '../../eventBus';

const createTrimMachine = (context) =>
  Machine(
    {
      invoke: [
        { id: 'select', src: fromEventBus('trim', () => context.eventBuses.select, 'SELECTED') },
        { src: fromEventBus('trim', () => context.eventBuses.hovering, 'HOVERING') },
        { src: fromEventBus('watershed', () => context.eventBuses.canvas, 'COORDINATES') },
        { id: 'arrays', src: fromEventBus('trim', () => context.eventBuses.arrays, []) },
      ],
      context: {
        x: null,
        y: null,
        hovering: null,
        label: context.selected,
      },
      on: {
        COORDINATES: { actions: 'setCoordinates' },
        HOVERING: { actions: 'setHovering' },
        SELECTED: { actions: 'setLabel' },
        mouseup: [
          { cond: 'onLabel', actions: (c, e, m) => console.log('trim', c, e, m) },
          { actions: 'select' },
        ],
      },
    },
    {
      guards: {
        onLabel: (ctx) => ctx.hovering.includes(ctx.label),
      },
      actions: {
        setCoordinates: assign({ x: (_, evt) => evt.x, y: (_, evt) => evt.y }),
        setHovering: assign({ hovering: (_, evt) => evt.hovering }),
        setLabel: assign({ label: (_, evt) => evt.selected }),
        select: send({ type: 'SELECT' }, { to: 'select' }),
        trim: send(
          (ctx) => ({
            type: 'EDIT',
            action: 'trim_pixels',
            args: {
              label: ctx.label,
              x: ctx.x,
              y: ctx.y,
            },
          }),
          { to: 'arrays' }
        ),
      },
    }
  );

export default createTrimMachine;
