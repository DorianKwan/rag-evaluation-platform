-- CreateEnum
CREATE TYPE "RunStatus" AS ENUM ('pending', 'running', 'success', 'failed', 'error');

-- CreateEnum
CREATE TYPE "TestCaseStatus" AS ENUM ('pending', 'running', 'success', 'failed', 'error');

-- CreateTable
CREATE TABLE "dataset" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "dataset_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "test_case" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "user_input" TEXT NOT NULL,
    "reference" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "test_case_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "eval_run" (
    "id" TEXT NOT NULL,
    "dataset_id" TEXT NOT NULL,
    "status" "RunStatus" NOT NULL DEFAULT 'pending',
    "webhook_url" TEXT,
    "total_count" INTEGER NOT NULL,
    "pass_threshold" DOUBLE PRECISION NOT NULL DEFAULT 0.7,
    "error_message" TEXT,
    "started_at" TIMESTAMP(3),
    "completed_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "eval_run_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "eval_test_case" (
    "id" TEXT NOT NULL,
    "eval_run_id" TEXT NOT NULL,
    "status" "TestCaseStatus" NOT NULL DEFAULT 'pending',
    "webhook_url" TEXT,
    "user_input" TEXT NOT NULL,
    "reference" TEXT NOT NULL,
    "model_response" TEXT,
    "passed" BOOLEAN,
    "score" DOUBLE PRECISION,
    "error_message" TEXT,
    "attempt_count" INTEGER NOT NULL DEFAULT 0,
    "last_error" TEXT,
    "started_at" TIMESTAMP(3),
    "completed_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "eval_test_case_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "eval_run_dataset_id_idx" ON "eval_run"("dataset_id");

-- CreateIndex
CREATE INDEX "eval_run_status_idx" ON "eval_run"("status");

-- CreateIndex
CREATE INDEX "eval_test_case_eval_run_id_status_idx" ON "eval_test_case"("eval_run_id", "status");

-- AddForeignKey
ALTER TABLE "test_case" ADD CONSTRAINT "test_case_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "dataset"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "eval_run" ADD CONSTRAINT "eval_run_dataset_id_fkey" FOREIGN KEY ("dataset_id") REFERENCES "dataset"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "eval_test_case" ADD CONSTRAINT "eval_test_case_eval_run_id_fkey" FOREIGN KEY ("eval_run_id") REFERENCES "eval_run"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
