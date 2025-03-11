import Fastify from 'fastify';
import fastifyStatic from '@fastify/static';
import path from 'path';
import { routes } from './routes/index';

const fastify = Fastify({ logger: true });

// Serve static files from frontend/public (relative to project root)
fastify.register(fastifyStatic, {
  root: path.join(__dirname, '../../frontend/public'),
  prefix: '/',
});

// Register API routes
fastify.register(routes, { prefix: '/api' });

const port = process.env.PORT || 3000; // Use env var for flexibility

const start = async () => {
  try {
    await fastify.listen({ port: Number(port), host: '0.0.0.0' }); // 0.0.0.0 for Docker
    console.log(`Server running on http://localhost:${port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
