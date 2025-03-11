import { FastifyPluginAsync } from 'fastify';
import { getItems, addItem } from '../db/neo4j';

export const routes: FastifyPluginAsync = async (fastify) => {
  fastify.get('/', async (request, reply) => {
    const items = await getItems();
    reply.send(items);
  });

  fastify.post('/add', async (request, reply) => {
    const { name } = request.body as { name: string };
    await addItem(name);
    reply.header('Content-Type', 'text/html');
    reply.send(`<li>${name}</li>`);
  });
};
